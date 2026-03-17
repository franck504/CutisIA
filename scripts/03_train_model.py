import os
import argparse
import matplotlib.pyplot as plt
import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.applications import MobileNetV3Small
from tensorflow.keras.preprocessing.image import ImageDataGenerator

def train_model(data_dir, epochs=20, batch_size=32, model_type="MobileNetV3"):
    """
    Trains a MobileNetV3 model on the cleaned dataset and exports to TFLite.
    """
    # 1. Dataset Loading & Augmentation
    datagen = ImageDataGenerator(
        rescale=1./255,
        validation_split=0.2,
        rotation_range=20,
        width_shift_range=0.2,
        height_shift_range=0.2,
        shear_range=0.2,
        zoom_range=0.2,
        horizontal_flip=True,
        fill_mode='nearest'
    )

    train_generator = datagen.flow_from_directory(
        data_dir,
        target_size=(224, 224),
        batch_size=batch_size,
        class_mode='categorical',
        subset='training'
    )

    val_generator = datagen.flow_from_directory(
        data_dir,
        target_size=(224, 224),
        batch_size=batch_size,
        class_mode='categorical',
        subset='validation'
    )

    num_classes = len(train_generator.class_indices)
    print(f"Detected {num_classes} classes: {list(train_generator.class_indices.keys())}")

    # 2. Model Creation (Transfer Learning)
    base_model = MobileNetV3Small(input_shape=(224, 224, 3), include_top=False, weights='imagenet')
    base_model.trainable = False  # Freeze base layers

    model = models.Sequential([
        base_model,
        layers.GlobalAveragePooling2D(),
        layers.Dropout(0.2),
        layers.Dense(num_classes, activation='softmax')
    ])

    model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])

    # 3. Training
    os.makedirs('models', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    checkpoint = tf.keras.callbacks.ModelCheckpoint(
        'models/best_model.h5', monitor='val_accuracy', save_best_only=True, mode='max'
    )
    early_stop = tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=5)

    print("\nStarting training...")
    history = model.fit(
        train_generator,
        epochs=epochs,
        validation_data=val_generator,
        callbacks=[checkpoint, early_stop]
    )

    # 4. Save History Plot
    plt.figure(figsize=(12, 4))
    plt.subplot(1, 2, 1)
    plt.plot(history.history['accuracy'], label='train')
    plt.plot(history.history['val_accuracy'], label='val')
    plt.title('Accuracy')
    plt.legend()
    
    plt.subplot(1, 2, 2)
    plt.plot(history.history['loss'], label='train')
    plt.plot(history.history['val_loss'], label='val')
    plt.title('Loss')
    plt.legend()
    plt.savefig('logs/training_history.png')
    print("Training history plot saved to logs/training_history.png")

    # 5. TFLite Conversion
    print("\nConverting model to TFLite...")
    best_model = tf.keras.models.load_model('models/best_model.h5')
    converter = tf.lite.TFLiteConverter.from_keras_model(best_model)
    tflite_model = converter.convert()

    with open('models/modele_cutanee.tflite', 'wb') as f:
        f.write(tflite_model)
    print("Model converted and saved to models/modele_cutanee.tflite")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Skin Disease Detection Model")
    parser.add_argument("--data_dir", type=str, required=True, help="Path to cleaned dataset")
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--batch_size", type=int, default=32)
    
    args = parser.parse_args()
    train_model(args.data_dir, args.epochs, args.batch_size)
