import numpy as np
from PIL import Image
import png

path = './test/ruru.jpg'
save_path = './test/secret_result.png'
n = 10
t = 5

def insert_text_chunk(src_png, dst_png, text):
    reader = png.Reader(filename=src_png)
    chunks = reader.chunks()
    chunk_list = list(chunks)
    chunk_item = tuple([b'tEXt', text])
    chunk_list.insert(1, chunk_item)

    with open(dst_png, 'wb') as dst_file:
        png.write_chunks(dst_file, chunk_list)
 
def read_text_chunk(src_png, index=1):
    reader = png.Reader(filename=src_png)
    chunks = reader.chunks()
    chunk_list = list(chunks)   
    img_extra = chunk_list[index][1]
    img_extra = img_extra.decode()
    img_extra = img_extra.split(" ")
    return img_extra

def gcd(a,b):
    while a!=0:
        a,b = b%a,a
    return b

def findModReverse(a,m):
    if abs(gcd(a,m)) != 1:
        print(f"error: {a}, {m}, {gcd(a,m)}")
        return None
    u1,u2,u3 = 1,0,a
    v1,v2,v3 = 0,1,m
    while v3 != 0:
        q = u3 // v3
        v1, v2, v3, u1, u2, u3 = (u1-q*v1), (u2-q*v2), (u3-q*v3), v1, v2, v3
    return u1 % m

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
        print("\r[" + ">" + " "*59 + "] {:.2f}%".format(0), end=' ')
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

        secret_red = secret_red % 257
        secret_green = secret_green % 257
        secret_blue = secret_blue % 257

        bitmap_text = ""
        for p in range(0, secret_red.shape[0]):
            for q in range(0, secret_red.shape[1]):
                if(secret_red[p][q] >= 256):
                    bitmap_text += "1" + " " + str(p) + " " + str(q) + " "
                if(secret_green[p][q] >= 256):
                    bitmap_text += "2" + " " + str(p) + " " + str(q) + " "
                if(secret_blue[p][q] >= 256):
                    bitmap_text += "3" + " " + str(p) + " " + str(q) + " "

        secret_img = np.stack([secret_red, secret_green, secret_blue], axis=-1)
        secret_img = Image.fromarray(secret_img.astype(np.uint8))
        secret_img.save('./test/secret_{}.png'.format(i+1))

        insert_text_chunk('./test/secret_{}.png'.format(i+1), './test/secret_{}.png'.format(i+1), bitmap_text.encode())

        print("\r["+"="*int((i+1)/n*60)+"\b>"*((int((i+1)/n*60))!=60)+" "*(60-(int((i+1)/n*60)))+"] {:.2f}%".format((i+1)/n*100), end=' ')
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

        bitmap = read_text_chunk(img_path, 1)
        for idx in range(0, bitmap.__len__(), 3):
            if(bitmap[idx] == '1'):
                img_red[int(bitmap[idx+1])][int(bitmap[idx+2])] = 256
            if(bitmap[idx] == '2'):
                img_green[int(bitmap[idx+1])][int(bitmap[idx+2])] = 256
            if(bitmap[idx] == '3'):
                img_blue[int(bitmap[idx+1])][int(bitmap[idx+2])] = 256

        x, y = 1, 1
        for j in range(list.__len__()):
            if(j != i):
                x *= list[j]
                y *= list[j] - list[i]

        div = x * findModReverse(y, 257) % 257

        img_red *= div
        img_green *= div
        img_blue *= div
        
        secret_red += img_red % 257
        secret_green += img_green % 257
        secret_blue += img_blue % 257
        print("\r["+"="*int((i+1)/list.__len__()*60)+"\b>"*((int((i+1)/list.__len__()*60))!=60)+" "*(60-(int((i+1)/list.__len__()*60)))+"] {:.2f}%".format((i+1)/list.__len__()*100), end=' ')

    secret_red = secret_red % 257
    secret_green = secret_green % 257
    secret_blue = secret_blue % 257

    secret_img = np.stack([secret_red, secret_green, secret_blue], axis=-1)
    secret_img = Image.fromarray(secret_img.astype(np.uint8))
    secret_img.save('./test/secret_result.png')
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
    shamir_decode(save_path, [2, 3, 4, 7, 9], red_channel.shape)
    shamir_confirm(path, save_path)