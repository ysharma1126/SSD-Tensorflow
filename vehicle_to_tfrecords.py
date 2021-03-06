# Copyright 2016 The TensorFlow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""Convert a dataset to TFRecords format, which can be easily integrated into
a TensorFlow pipeline.
"""
import tensorflow as tf
import os
import sys
import json
from collections import defaultdict
import pprint

from datasets.vehicle_common import LABELS
from datasets.dataset_utils import int64_feature, float_feature, bytes_feature

def annotationsparse(annotations_file):
    annotations = defaultdict(list)
    fyle = open(annotations_file)
    for lyne in fyle:
        trackid, xmin, ymin, xmax, ymax, frame, lost, occluded, generated, label = lyne.split()
        #print(lyne.split())
        if (int(lost) == 0 and int(occluded) == 0):
            annotations[int(frame)].append((int(xmin), int(ymin), int(xmax), int(ymax)))
    fyle.close()
    return annotations

def write_images_from_directory(set_directory_name, set_directory_path, annotations_file, tfrecord_writer):
    sequences = sorted(os.listdir(set_directory_path))
    for sequence in sequences:
        #annotations_frames = annotations_file[set_directory_name][sequence]['frames']
        image_path = os.path.join(set_directory_path, sequence + '/')
        images = sorted(os.listdir(image_path))

        input_height = 480
        input_width = 640
        input_depth = 3

        bboxes = []
        labels = []
        labels_text = []
        difficult = []
        truncated = []

        for frame in images:
            frame_num = int(frame[:-4])
            #print(frame_num)
            if (frame_num <= 3600):
                #sys.stdout.write('\r>> Annotating image %d' % (frame_num))
                print('Annotating image' + str(frame_num))
                bboxes_f = []
                labels_f = []
                labels_text_f = []
                difficult_f = []
                truncated_f = []

                object_dicts_list = []
                object_dicts_list = annotations_file[frame_num]

                for object_dict in object_dicts_list:
                    label_f = 'car'
                    labels_f.append(int(LABELS[label_f][0]))
                    labels_text_f.append(label_f.encode('ascii'))

                    xmin = float(object_dict[0])/input_width
                    ymin = float(object_dict[1])/input_height
                    xmax = float(object_dict[2])/input_width
                    ymax = float(object_dict[3])/input_height

                    bboxes_f.append([xmin, ymin, xmax, ymax])
                    difficult_f.append(0)
                    truncated_f.append(0)
                bboxes.append(bboxes_f)
                labels.append(labels_f)
                labels_text.append(labels_text_f)
                difficult.append(difficult_f)
                truncated.append(truncated_f)
        print(len(bboxes))

        for i, frame in enumerate(images):
            frame_num = int(frame[:-4])
            if (frame_num <= 3600):
                #sys.stdout.write('\r>> Converting image %d' % (frame_num))
                #sys.stdout.flush()
                print('Converting image' + str(frame_num))

                image_file = image_path+frame
                image_data = tf.gfile.FastGFile(image_file, 'rb').read()

                xmin = []
                ymin = []
                xmax = []
                ymax = []

                for b in bboxes[i]:
                    [l.append(point) for l, point in zip([xmin, ymin, xmax, ymax], b)]

                image_format = b'JPEG'
                example = tf.train.Example(features=tf.train.Features(feature={
                    'image/height': int64_feature(input_height),
                    'image/width': int64_feature(input_width),
                    'image/channels': int64_feature(input_depth),
                    'image/shape': int64_feature([input_height, input_width, input_depth]),
                    'image/object/bbox/xmin': float_feature(xmin),
                    'image/object/bbox/xmax': float_feature(xmax),
                    'image/object/bbox/ymin': float_feature(ymin),
                    'image/object/bbox/ymax': float_feature(ymax),
                    'image/object/bbox/label': int64_feature(labels[i]),
                    'image/object/bbox/label_text': bytes_feature(labels_text[i]),
                    'image/object/bbox/difficult': int64_feature(difficult[i]),
                    'image/object/bbox/truncated': int64_feature(truncated[i]),
                    'image/format': bytes_feature(image_format),
                    'image/encoded': bytes_feature(image_data)}))
                tfrecord_writer.write(example.SerializeToString())

def main(_):
    print('Dataset directory: ./datasets')
    print('Output directory: ./datasets')
    print('Output name: vehicle')

    tf_filename_train = './datasets/vehicle_train.tfrecord'
    if tf.gfile.Exists(tf_filename_train):
        print('Dataset file: vehicle_train already exist. Exiting without re-creating them.')
        return
    tf_filename_val = './datasets/vehicle_test.tfrecord'
    if tf.gfile.Exists(tf_filename_val):
        print('Dataset file: vehicle_val already exists. Exiting without re-creating them.')
        return

    """
    What this means is that files should be stored as follows:

    datasets/
        JPEGImages/
            set01/
                V000/
                v001/
                ....
                ....
            set02/
                ....
            set03/
                ....
        Annotations/
            annotations.json
    """

    jpeg_path = os.path.join('./datasets', 'JPEGImages_Vehicle/')
    annotations_path = os.path.join('./datasets', 'Annotations_Vehicle/')
    print('jpeg path: ', jpeg_path)
    print('annotations_path: ', annotations_path)
    set_directories = sorted(os.listdir(jpeg_path))
    """
    i = 0
    train_directories = []
    test_directories = []
    for set_directory in set_directories:
        if (i < 5):
            train_directories.append(set_directory)
        else:
            test_directories.append(set_directory)
        i += 1
    
    annotations_file = annotations_path+'annotations.json'
    annotations_text = open(annotations_file)
    annotations_file = json.load(annotations_text)
    """
    with tf.python_io.TFRecordWriter(tf_filename_train) as tfrecord_writer:
        #for set_directory in train_directories:
        for set_directory in set_directories:
            if (set_directory == '1_Ave_7' or set_directory == '1_Ave_12' or set_directory == '1_Ave_17'):
                annotations_file = annotations_path+set_directory+'.txt'
                #print(annotations_file)
                set_directory_path = os.path.join(jpeg_path, set_directory + '/')
                write_images_from_directory(set_directory, set_directory_path, annotationsparse(annotations_file), tfrecord_writer)

    """
    I have val and train as the same here.  Keeping it as we want results lol
    """

    with tf.python_io.TFRecordWriter(tf_filename_val) as tfrecord_writer:
        #for set_directory in test_directories:
        for set_directory in set_directories:
            if (set_directory == '1_Ave_7' or set_directory == '1_Ave_12' or set_directory == '1_Ave_17'):
                annotations_file = annotations_path+set_directory+'.txt'
                #print(annotations_file)
                set_directory_path = os.path.join(jpeg_path, set_directory + '/')
                write_images_from_directory(set_directory, set_directory_path, annotationsparse(annotations_file), tfrecord_writer)
    print('\nFinished converting the Vehicle dataset!')

if __name__ == '__main__':
    tf.app.run()

