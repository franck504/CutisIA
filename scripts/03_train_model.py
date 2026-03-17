import os
import argparse
import matplotlib.pyplot as plt
import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.applications import MobileNetV3Small

def train_model(data_dir, epochs=20, fine_tune_epochs=10, batch_size=32):
    """
    Two-stage training: 
    1. Warm-up (Frozen base)
    2. Fine-tuning (Unfrozen top layers)
    """
    # 0. Optimization & Mixed Precision
    device = "GPU" if tf.config.list_physical_devices('GPU') else "CPU"
    print(f"\n--- Using Hardware: {device} ---")
    
    if device == "GPU":
        from tensorflow.keras import mixed_precision
        policy = mixed_precision.Policy('mixed_float16')
        mixed_precision.set_global_policy(policy)
        print("Mixed precision enabled (float16).")

    # 1. Dataset Loading
    print("\nLoading datasets...")
    train_ds = tf.keras.utils.image_dataset_from_directory(
        data_dir, validation_split=0.2, subset="training", seed=123,
        image_size=(224, 224), batch_size=batch_size, label_mode='categorical'
    )
    val_ds = tf.keras.utils.image_dataset_from_directory(
        data_dir, validation_split=0.2, subset="validation", seed=123,
        image_size=(224, 224), batch_size=batch_size, label_mode='categorical'
    )

    class_names = train_ds.class_names
    num_classes = len(class_names)
    
    # Data Augmentation (Moved here to keep the model TFLite-compatible)
    augmentation = models.Sequential([
        layers.RandomFlip("horizontal"),
        layers.RandomRotation(0.1),
        layers.RandomZoom(0.1),
    ])

    AUTOTUNE = tf.data.AUTOTUNE
    def prepare(ds, augment=False):
        # Rescale here
        ds = ds.map(lambda x, y: (x / 255.0, y), num_parallel_calls=AUTOTUNE)
        if augment:
            ds = ds.map(lambda x, y: (augmentation(x, training=True), y), num_parallel_calls=AUTOTUNE)
        return ds.cache().prefetch(buffer_size=AUTOTUNE)

    train_ds = prepare(train_ds.shuffle(1000), augment=True)
    val_ds = prepare(val_ds)

    # 2. Model Creation (Clean for TFLite)
    base_model = MobileNetV3Small(input_shape=(224, 224, 3), include_top=False, weights='imagenet')
    base_model.trainable = False 

    model = models.Sequential([
        layers.Input(shape=(224, 224, 3)),
        base_model,
        layers.GlobalAveragePooling2D(),
        layers.Dropout(0.5), # Increased from 0.3 to 0.5 to fight overfitting
        layers.Dense(num_classes, activation='softmax', dtype='float32')
    ])

    # 3. Phase 1: Warm-up
    print(f"\n--- Phase 1: Warm-up ({epochs} epochs) ---")
    model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
    
    os.makedirs('models', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    checkpoint = tf.keras.callbacks.ModelCheckpoint(
        'models/best_model_warmup.keras', monitor='val_accuracy', save_best_only=True, mode='max'
    )

    # Callbacks for better convergence
    lr_reducer = tf.keras.callbacks.ReduceLROnPlateau(
        monitor='val_loss', factor=0.5, patience=3, min_lr=1e-6
    )

    history = model.fit(
        train_ds, validation_data=val_ds, epochs=epochs, 
        callbacks=[checkpoint, lr_reducer], verbose=1
    )

    # 4. Phase 2: Fine-tuning
    print(f"\n--- Phase 2: Fine-tuning ({fine_tune_epochs} epochs) ---")
    base_model.trainable = True
    
    model.compile(
        optimizer=tf.keras.optimizers.Adam(1e-5), 
        loss='categorical_crossentropy', 
        metrics=['accuracy']
    )

    checkpoint_ft = tf.keras.callbacks.ModelCheckpoint(
        'models/best_model_ft.keras', monitor='val_accuracy', save_best_only=True, mode='max'
    )

    history_ft = model.fit(
        train_ds, validation_data=val_ds, 
        epochs=epochs + fine_tune_epochs,
        initial_epoch=history.epoch[-1],
        callbacks=[checkpoint_ft],
        verbose=1
    )

    # 5. Save Plots
    acc = history.history['accuracy'] + history_ft.history['accuracy']
    val_acc = history.history['val_accuracy'] + history_ft.history['val_accuracy']
    plt.figure(figsize=(8, 8))
    plt.subplot(2, 1, 1)
    plt.plot(acc, label='Training Accuracy')
    plt.plot(val_acc, label='Validation Accuracy')
    plt.plot([epochs-1, epochs-1], plt.ylim(), label='Start Fine Tuning')
    plt.title('Training & Validation Accuracy')
    plt.legend()
    plt.savefig('logs/training_history_ft.png')

    # 6. TFLite Conversion (Robust with SELECT_TF_OPS)
    print("\nConverting model to TFLite (Compatibility Mode)...")
    # In some versions, reloading the model helps clean the graph
    best_model = tf.keras.models.load_model('models/best_model_ft.keras')
    
    # Use from_keras_model but with explicit support for all TF ops as backup
    converter = tf.lite.TFLiteConverter.from_keras_model(best_model)
    
    # Fix for 'Relu6' or 'AddV2' missing errors
    converter.target_spec.supported_ops = [
        tf.lite.OpsSet.TFLITE_BUILTINS,
        tf.lite.OpsSet.SELECT_TF_OPS 
    ]
    # Experimental: lowers some common TF ops to TFLite equivalents
    converter._experimental_lower_tensor_list_ops = True
    
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    
    try:
        tflite_model = converter.convert()
        with open('models/modele_cutanee_optimise.tflite', 'wb') as f:
            f.write(tflite_model)
        print("Success: models/modele_cutanee_optimise.tflite generated.")
    except Exception as e:
        print(f"Error during TFLite conversion: {e}")
        print("Attempting SavedModel fallback...")
        model.export('models/temporary_saved_model')
        converter = tf.lite.TFLiteConverter.from_saved_model('models/temporary_saved_model')
        converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS, tf.lite.OpsSet.SELECT_TF_OPS]
        tflite_model = converter.convert()
        with open('models/modele_cutanee_optimise.tflite', 'wb') as f:
            f.write(tflite_model)
        print("Success (Fallback): TFLite model generated via SavedModel.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Optimized Training with Fine-Tuning")
    parser.add_argument("--data_dir", type=str, required=True)
    parser.add_argument("--epochs", type=int, default=15, help="Warm-up epochs")
    parser.add_argument("--ft_epochs", type=int, default=10, help="Fine-tuning epochs")
    parser.add_argument("--batch_size", type=int, default=32)
    
    args = parser.parse_args()
    train_model(args.data_dir, args.epochs, args.ft_epochs, args.batch_size)
