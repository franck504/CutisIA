import os
import argparse
import matplotlib.pyplot as plt
import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.applications import MobileNetV3Small

def train_model(data_dir, epochs=20, batch_size=32):
    """
    Trains a MobileNetV3 model with optimized tf.data pipeline.
    """
    # 0. Hardware Detection & Optimization
    device = "GPU" if tf.config.list_physical_devices('GPU') else "CPU"
    print(f"\n--- Using Hardware: {device} ---")
    
    # Enable mixed precision for GPU if available (Modern GPUs)
    if device == "GPU":
        # Note: MobileNetV3 might not benefit much from mixed precision on older GPUs
        # but it's good practice for modern Colab T4/L4
        try:
            tf.keras.mixed_precision.set_global_policy('mixed_float16')
            print("Mixed precision enabled.")
        except:
            pass

    # 1. Dataset Loading (Modern API)
    print("\nLoading datasets...")
    train_ds = tf.keras.utils.image_dataset_from_directory(
        data_dir,
        validation_split=0.2,
        subset="training",
        seed=123,
        image_size=(224, 224),
        batch_size=batch_size,
        label_mode='categorical'
    )

    val_ds = tf.keras.utils.image_dataset_from_directory(
        data_dir,
        validation_split=0.2,
        subset="validation",
        seed=123,
        image_size=(224, 224),
        batch_size=batch_size,
        label_mode='categorical'
    )

    class_names = train_ds.class_names
    num_classes = len(class_names)
    print(f"Detected classes: {class_names}")

    # 2. Performance Optimization (Prefetch & Cache)
    # This maximizes GPU usage by preparing data in advance
    AUTOTUNE = tf.data.AUTOTUNE
    train_ds = train_ds.cache().shuffle(1000).prefetch(buffer_size=AUTOTUNE)
    val_ds = val_ds.cache().prefetch(buffer_size=AUTOTUNE)

    # 3. Data Augmentation Layer (runs on GPU)
    data_augmentation = models.Sequential([
        layers.RandomFlip("horizontal_and_vertical"),
        layers.RandomRotation(0.2),
        layers.RandomZoom(0.2),
    ])

    # 4. Model Creation (Transfer Learning)
    base_model = MobileNetV3Small(input_shape=(224, 224, 3), include_top=False, weights='imagenet')
    base_model.trainable = False

    model = models.Sequential([
        layers.Input(shape=(224, 224, 3)),
        data_augmentation,
        layers.Rescaling(1./255),
        base_model,
        layers.GlobalAveragePooling2D(),
        layers.Dropout(0.2),
        layers.Dense(num_classes, activation='softmax', dtype='float32') # Ensure float32 for output
    ])

    model.compile(
        optimizer='adam',
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )

    # 5. Training Callbacks
    os.makedirs('models', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    checkpoint = tf.keras.callbacks.ModelCheckpoint(
        'models/best_model.keras', monitor='val_accuracy', save_best_only=True, mode='max'
    )
    early_stop = tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=5)

    print("\nStarting training (with percentage progress)...")
    history = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=epochs,
        callbacks=[checkpoint, early_stop],
        verbose=1 # Ensure progress bar is visible
    )

    # 6. Save Plots
    plt.figure(figsize=(12, 4))
    plt.subplot(1, 2, 1)
    plt.plot(history.history['accuracy'], label='train')
    plt.plot(history.history['val_accuracy'], label='val')
    plt.title('Accuracy')
    plt.subplot(1, 2, 2)
    plt.plot(history.history['loss'], label='train')
    plt.plot(history.history['val_loss'], label='val')
    plt.title('Loss')
    plt.savefig('logs/training_history.png')
    print("\nTraining history plot saved to logs/training_history.png")

    # 7. TFLite Conversion
    print("Converting best model to TFLite...")
    best_model = tf.keras.models.load_model('models/best_model.keras')
    converter = tf.lite.TFLiteConverter.from_keras_model(best_model)
    tflite_model = converter.convert()

    with open('models/modele_cutanee.tflite', 'wb') as f:
        f.write(tflite_model)
    print("Model converted and saved to models/modele_cutanee.tflite")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Optimized Training for Colab")
    parser.add_argument("--data_dir", type=str, required=True)
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--batch_size", type=int, default=32)
    
    args = parser.parse_args()
    train_model(args.data_dir, args.epochs, args.batch_size)
