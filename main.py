from __future__ import print_function

import os
import time

import numpy as np
import tensorflow as tf
from tensorflow.examples.tutorials.mnist import input_data

from discriminator import *
from generator import generator
from utils import margin_loss


tf.logging.set_verbosity(tf.logging.INFO)
mnist = input_data.read_data_sets("MNIST_data", one_hot=True)

model_dir = 'model/'
data_dir = 'data/'
log_dir = 'log/'

lr = 1e-5
batch_size = 36
z_dim = 100
max_epochs = 1000
d_step = 50
g_step = 50
save_summary_steps = 100

# mnist image data
x_placeholder = tf.placeholder("float", shape=[batch_size, 28, 28, 1], name="x_placeholder")

with tf.variable_scope(tf.get_variable_scope()) as scope:
    Gz = generator(batch_size, z_dim)
    Dx = capsule_discriminator(x_placeholder, reuse=False)
    Dg = capsule_discriminator(Gz)

# loss function
g_loss = margin_loss(1, Dg)
d_loss_real = margin_loss(1, Dx)
d_loss_fake = margin_loss(0, Dg)
d_loss = d_loss_real + d_loss_fake

tf.summary.scalar("G loss", g_loss)
tf.summary.scalar("D loss", d_loss)
tf.summary.image("generated images", tf.reshape(Gz, [6*28, 6*28, 1]))
merged = tf.summary.merge_all()

thetas = tf.trainable_variables()
theta_d = [var for var in thetas if 'd_' in var.name]
theta_g = [var for var in thetas if 'g_' in var.name]

with tf.variable_scope(tf.get_variable_scope()) as scope:
    d_solver = tf.train.AdamOptimizer(learning_rate=lr).minimize(d_loss, var_list=theta_d)
    g_solver = tf.train.AdamOptimizer(learning_rate=lr).minimize(g_loss, var_list=theta_g)

saver = tf.train.Saver()

with tf.Session() as sess:
    writer = tf.summary.FileWriter(log_dir, sess.graph)
    sess.run(tf.global_variables_initializer())

    for epoch in range(max_epochs):
        x_image, _ = mnist.train.next_batch(batch_size)
        x_image = x_image.reshape([batch_size, 28, 28, 1])

        for step in range(d_step):
            d_loss_cur, _ = sess.run([d_loss, d_solver], feed_dict={x_placeholder: x_image})

        for step in range(g_step):
            g_loss_cur, _ = sess.run([g_loss, g_solver], feed_dict={x_placeholder: x_image})

        print("Time {3}, Step {0}, Discriminator Loss {1:f}, Generator Loss {2:f}".format(
            epoch, d_loss_cur, g_loss_cur, time.strftime("%b %d, %H:%M:%S")))

        if epoch % 100 == 99:
            saver.save(sess, os.path.join(model_dir, "model.ckpt"), global_step=epoch)
            summary = sess.run(merged, feed_dict={x_placeholder: x_image})
