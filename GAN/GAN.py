import numpy as np
import matplotlib.pyplot as plt
import os

from keras.layers import Input, Dense, Flatten, Reshape, BatchNormalization, Activation
from keras.layers.advanced_activations import LeakyReLU
from keras.optimizers import Adam
from keras.models import Sequential, Model
from keras.utils import plot_model

os.environ["CUDA_VISIBLE_DEVICES"] = "2"
plt.switch_backend('agg')

class GAN():
    
    def __init__(self):
        self.row = 28
        self.col = 28
        self.channel = 1
        self.img_shape = (self.row, self.col, self.channel)
        self.latent_dim = 100

        optimizer = Adam(0.0002, 0.5)
        
        self.discriminator = self.build_discriminator()
        self.discriminator.compile(loss='binary_crossentropy', optimizer=optimizer, metrics=['accuracy'])
        self.discriminator.trainable = False

        self.generator = self.build_generator()

        noise = Input(shape=(self.latent_dim,))
        img = self.generator(noise)
        
        pred = self.discriminator(img)

        self.combined = Model(noise, pred)
        self.combined.compile(loss='binary_crossentropy', optimizer=optimizer)


    def build_generator(self):

        model = Sequential()

        model.add(Dense(256, input_dim=self.latent_dim))
        model.add(LeakyReLU(alpha=0.2))
        model.add(BatchNormalization(momentum=0.8))
        model.add(Dense(512))
        model.add(LeakyReLU(alpha=0.2))
        model.add(BatchNormalization(momentum=0.8))
        model.add(Dense(1024))
        model.add(LeakyReLU(alpha=0.2))
        model.add(BatchNormalization(momentum=0.8))
        model.add(Dense(np.prod(self.img_shape), activation='tanh'))
        model.add(Reshape(self.img_shape))

        model.summary()
        plot_model(model, to_file='generator.png')

        noise = Input(shape=(self.latent_dim,))
        img = model(noise)

        return Model(noise, img)

    def build_discriminator(self):

        model = Sequential()

        model.add(Flatten(input_shape=self.img_shape))
        model.add(Dense(512))
        model.add(LeakyReLU(alpha=0.2))
        model.add(Dense(256))
        model.add(LeakyReLU(alpha=0.2))
        model.add(Dense(1, activation='sigmoid'))
        
        model.summary()
        plot_model(model, to_file='discriminator.png')

        img = Input(shape=self.img_shape)
        label = model(img)

        return Model(img, label)

    def train(self, epochs, batch_size=128, sample_interval=50):

        f = np.load('../mnist.npz')
        X_train = f['x_train']
        f.close()

        X_train = X_train / 127.5 - 1.
        X_train = np.expand_dims(X_train, axis=3)

        real = np.ones((batch_size, 1))
        fake = np.zeros((batch_size, 1))

        for epoch in range(epochs):
            idx = np.random.randint(0, X_train.shape[0], batch_size)
            real_imgs = X_train[idx]

            noise = np.random.normal(0, 1, (batch_size, self.latent_dim))
            fake_imgs = self.generator.predict(noise)

            d_loss_real = self.discriminator.train_on_batch(real_imgs, real)
            d_loss_fake = self.discriminator.train_on_batch(fake_imgs, fake)
            d_loss = 0.5 * np.add(d_loss_real, d_loss_fake)

            noise = np.random.normal(0, 1, (batch_size, self.latent_dim))
            g_loss = self.combined.train_on_batch(noise, real)

            print("%d [D loss: %f, acc.: %.2f%%] [G loss: %f]" % (epoch, d_loss[0], 100*d_loss[1], g_loss))

            if epoch % sample_interval == 0:
                self.sample_images(epoch)

    def sample_images(self, epoch):
        r, c = 5, 5
        noise = np.random.normal(0, 1, (r * c, self.latent_dim))
        gen_imgs = self.generator.predict(noise)
        gen_imgs = 0.5 * gen_imgs + 0.5

        fig, axs = plt.subplots(r, c)
        cnt = 0
        for i in range(r):
            for j in range(c):
                axs[i,j].imshow(gen_imgs[cnt, :,:,0], cmap='gray')
                axs[i,j].axis('off')
                cnt += 1    
        fig.savefig("images/%d.png" % epoch)
        plt.close()


if __name__ == '__main__':
    gan = GAN()
    gan.train(epochs=30000, batch_size=32, sample_interval=200)
