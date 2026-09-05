# SIH26188 Document Verification API
import sys
import types
import os

# Ensure tf-keras / keras compatibility shim for DeepFace in non-TF environments
if "tensorflow" not in sys.modules:
    try:
        import tensorflow
    except ImportError:
        try:
            import numpy as np
            import keras
            
            tf_shim = types.ModuleType("tensorflow")
            tf_shim.__version__ = "2.15.0"
            tf_shim.keras = keras
            tf_shim.float32 = np.float32
            tf_shim.float64 = np.float64
            tf_shim.int32 = np.int32
            tf_shim.int64 = np.int64
            tf_shim.uint8 = np.uint8
            tf_shim.bool = np.bool_
            tf_shim.constant = np.array
            tf_shim.convert_to_tensor = np.asarray
            
            import logging
            tf_shim.get_logger = lambda: logging.getLogger("tensorflow")
            
            sys.modules["tensorflow"] = tf_shim
            sys.modules["tensorflow.keras"] = keras
            for attr in ['models', 'layers', 'backend', 'applications', 'utils', 'callbacks', 'initializers', 'optimizers', 'preprocessing']:
                if hasattr(keras, attr):
                    sys.modules[f'tensorflow.keras.{attr}'] = getattr(keras, attr)
        except Exception:
            pass