
import cv2
import numpy as np
import tensorflow as tf
from tensorflow.keras.applications.inception_v3 import InceptionV3, preprocess_input
from tensorflow.keras.preprocessing import image
from tensorflow.keras.models import Model
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.layers import Input, Dense, Embedding, LSTM
from tensorflow.keras.layers import add
from tensorflow.keras.callbacks import ModelCheckpoint
from pickle import load
import os

def processVid(videoPath):

    '''
    To obtain the necessary pre-requisites for the provided Python code, follow these steps:

1. **Pre-trained InceptionV3 model weights**:
   - You can download the pre-trained InceptionV3 model weights from the TensorFlow Keras applications page or from the official TensorFlow GitHub repository.
   - Here's how you can load the InceptionV3 model in TensorFlow:
     ```python
     from tensorflow.keras.applications.inception_v3 import InceptionV3

     # Load the InceptionV3 model with pre-trained weights
     inception_model = InceptionV3(weights='imagenet')
     ```

2. **A pre-trained tokenizer to tokenize the captions**:
   - You need a tokenizer that was trained on a dataset of captions. This tokenizer should be able to convert words into numerical tokens and vice versa.
   - You can train your tokenizer on a dataset of captions or use a pre-trained tokenizer available online.
   - After obtaining the tokenizer, you can load it using Python's `pickle` module:
     ```python
     from pickle import load

     # Load the tokenizer from a pickle file
     tokenizer = load(open('tokenizer.pkl', 'rb'))
     ```

3. **The model architecture stored in a .h5 file**:
   - The model architecture should be saved in a .h5 file using TensorFlow's model-saving functionalities.
   - You can save the model architecture and weights using the `save()` method:
     ```python
     # Assuming 'model' is your Keras model
     model.save('model.h5')
     ```
   - Then, you can load the model using the `load_model()` function from Keras:
     ```python
     from tensorflow.keras.models import load_model

     # Load the model architecture and weights from the .h5 file
     model = load_model('model.h5')
     ```

Make sure you have these pre-requisites available before running the provided Python code for generating text captions for a video. Adjust the paths and filenames according to where you have saved these pre-requisites on your system.


    :param videoPath:
    :return:
    '''



    # Load the pre-trained InceptionV3 model trained on ImageNet data
    inception_model = InceptionV3(weights='imagenet')
    inception_model = Model(inception_model.input, inception_model.layers[-2].output)

    # Load the tokenizer and model architecture
    tokenizer = load(open('tokenizer.pkl', 'rb'))
    max_length = 34
    embedding_dim = 200

    inputs1 = Input(shape=(2048,))
    fe1 = Dense(embedding_dim, activation='relu')(inputs1)
    inputs2 = Input(shape=(max_length,))
    se1 = Embedding(len(tokenizer.word_index) + 1, embedding_dim, mask_zero=True)(inputs2)
    se2 = LSTM(embedding_dim)(se1)
    decoder1 = add([fe1, se2])
    decoder2 = Dense(embedding_dim, activation='relu')(decoder1)
    outputs = Dense(len(tokenizer.word_index) + 1, activation='softmax')(decoder2)
    model = Model(inputs=[inputs1, inputs2], outputs=outputs)

    model.load_weights('model_weights.h5')

    # Function to preprocess the input frame
    def preprocess_frame(frame):
        img = cv2.resize(frame, (299, 299))
        img = image.img_to_array(img)
        img = np.expand_dims(img, axis=0)
        img = preprocess_input(img)
        return img

    # Function to generate caption for a frame
    def generate_caption(frame):
        features = inception_model.predict(preprocess_frame(frame))
        caption = 'startseq'
        for i in range(max_length):
            sequence = tokenizer.texts_to_sequences([caption])[0]
            sequence = pad_sequences([sequence], maxlen=max_length)
            yhat = model.predict([features, sequence], verbose=0)
            yhat = np.argmax(yhat)
            word = tokenizer.index_word[yhat]
            caption += ' ' + word
            if word == 'endseq':
                break
        return caption.split()[1:-1]

    # Read the video file
    video_path = videoPath
    cap = cv2.VideoCapture(video_path)

    # Process each frame and generate captions
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        caption = generate_caption(frame)
        print(' '.join(caption))

    cap.release()
    cv2.destroyAllWindows()
