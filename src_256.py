import numpy as np
from PIL import Image

path = './test/ruru.jpg'
save_path = './test/secret_result.png'
n = 10
t = 5

def parse_img(path):
    img = Image.open(path)
    if img == None:
        print(f"open image falid: {path}")
        exit(0)
    if img.mode != 'RGB':
        img = img.convert('RGB')
    img_array = np.array(img)
    red_channel = img_array[:, :, 0].astype(np.int32)
    green_channel = img_array[:, :, 1].astype(np.int32)
    blue_channel = img_array[:, :, 2].astype(np.int32)
    
    return red_channel, green_channel, blue_channel, img_array.shape

def shamir_encode(n, t, red_channel, green_channel, blue_channel, rand_matrix):
    print("encoding...")
    for i in range(n):
        print("\r[" + ">" + " "*59 + "] {:.2f}%".format((i+1)/n*100), end=' ')
        secret_red = np.zeros(shape=red_channel.shape)
        secret_green = np.zeros(shape=green_channel.shape)
        secret_blue = np.zeros(shape=blue_channel.shape)

        secret_red += red_channel
        secret_green += green_channel
        secret_blue += blue_channel

        for j in range(1, t):
            secret_red += rand_matrix[:, :, 0, j] * ((i+1)**(j))
            secret_green += rand_matrix[:, :, 1, j] * ((i+1)**(j))
            secret_blue += rand_matrix[:, :, 2, j] * ((i+1)**(j))

        secret_red = secret_red % 256
        secret_green = secret_green % 256
        secret_blue = secret_blue % 256

        secret_img = np.stack([secret_red, secret_green, secret_blue], axis=-1)
        secret_img = Image.fromarray(secret_img.astype(np.uint8))
        secret_img.save('./test/secret_{}.png'.format(i+1))
        print("\r[" + "="*int((i+1)/n*60) + "\b>"*((int((i+1)/n*60))!=60) + " "*(60-(int((i+1)/n*60))) + "] {:.2f}%".format((i+1)/n*100), end=' ')
    print("\n[+] successfully generated {} secret".format(n))

def shamir_decode(path, list, shape):
    secret_red = np.zeros(shape=shape)
    secret_green = np.zeros(shape=shape)
    secret_blue = np.zeros(shape=shape)
    print("decoding...")
    for i in range(list.__len__()):
        print("\r[" + ">" + " "*59 + "] {:.2f}%".format(0), end=' ')
        img_path = './test/secret_{}.png'.format(list[i])
        img_red, img_green, img_blue, shape = parse_img(img_path)
        img_red = img_red.astype(np.float32)
        img_green = img_green.astype(np.float32)
        img_blue = img_blue.astype(np.float32)

        x, y = 1, 1
        for j in range(list.__len__()):
            if(j != i):
                x *= list[j]
                y *= list[j] - list[i]

        div = x * pow(y, -1)

        img_red *= div
        img_green *= div
        img_blue *= div
        
        secret_red += img_red
        secret_green += img_green
        secret_blue += img_blue
        print("\r["+"="*int((i+1)/list.__len__()*60)+"\b>"*((int((i+1)/list.__len__()*60))!=60)+" "*(60-(int((i+1)/list.__len__()*60)))+"] {:.2f}%".format((i+1)/list.__len__()*100), end=' ')

    secret_red = secret_red % 256
    secret_green = secret_green % 256
    secret_blue = secret_blue % 256

    secret_img = np.stack([secret_red, secret_green, secret_blue], axis=-1)
    secret_img = Image.fromarray(secret_img.astype(np.uint8))
    secret_img.save(path)
    print("\n[+] successfully rebuilt the secret: {}".format(path))

def shamir_confirm(secret, rebuild):
    secret_red, secret_green, secret_blue, shape = parse_img(secret)
    rebuild_red, rebuild_green, rebuild_blue, shape = parse_img(rebuild)
    secret_sum = (secret_red + secret_green + secret_blue).sum()
    rebuild_sum = (rebuild_red + rebuild_green + rebuild_blue).sum()
    diff = 100 - (abs(secret_sum - rebuild_sum) / secret_sum * 100)
    print(f"[+] simulation: {diff:.2f}%")

if __name__ == '__main__':
    red_channel, green_channel, blue_channel, shape = parse_img(path)

    rand_matrix = np.random.randint(low=1, high=255, size=(shape[0], shape[1], 3, t))
    shamir_encode(n, t, red_channel, green_channel, blue_channel, rand_matrix)
    shamir_decode(save_path, [2, 3, 4, 5, 9], red_channel.shape)
    shamir_confirm(path, save_path)