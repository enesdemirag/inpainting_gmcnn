import os
import cv2
import numpy as np
import tensorflow as tf
from util.utils import generate_rect_mask, generate_stroke_mask
from options.options import TestOptions
from model.network import GMCNNModel

path_in = 'imgs/celebahq_256x256/'
path_out = 'results/celebahq_256x256/'

images = os.listdir(path_in)

config = TestOptions().parse()

model = GMCNNModel()

with tf.Session(config=tf.ConfigProto()) as sess:
    input_image_tf = tf.placeholder(dtype=tf.float32, shape=[1, config.img_shapes[0], config.img_shapes[1], 3])
    input_mask_tf = tf.placeholder(dtype=tf.float32, shape=[1, config.img_shapes[0], config.img_shapes[1], 1])

    output = model.evaluate(input_image_tf, input_mask_tf, config=config, reuse=False)
    output = (output + 1) * 127.5
    output = tf.minimum(tf.maximum(output[:, :, :, ::-1], 0), 255)
    output = tf.cast(output, tf.uint8)

    # load pretrained model
    vars_list = tf.get_collection(tf.GraphKeys.GLOBAL_VARIABLES)
    assign_ops = list(map(lambda x: tf.assign(x, tf.contrib.framework.load_variable(config.load_model_dir, x.name)), vars_list))
    sess.run(assign_ops)
    print('model loaded.')
    total_time = 0

    for img_file in images:
        
        image = cv2.imread(path_in + img_file)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        h, w, c = image.shape
        mask = generate_stroke_mask(im_size=[h, w])
        # mask = generate_rect_mask(im_size=[h, w, c], mask_size=[128, 128])

        # Original Image
        input_img = image.astype(np.uint8)

        # Masked Image
        image = image * (1-mask) + 255 * mask
        image = np.expand_dims(image, 0)
        mask = np.expand_dims(mask, 0)

        # Output Image
        result = sess.run(output, feed_dict={input_image_tf: image, input_mask_tf: mask})

        cv2.imwrite(str(path_out + 'original_' + img_file), input_img)
        cv2.imwrite(str(path_out + 'masked_' + img_file), image.astype(np.uint8))
        cv2.imwrite(str(path_out + 'output_' + img_file), result[0][:, :, ::-1])
        print(img_file, 'saved.')

print('done.')
