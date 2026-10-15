import os
root = r"C:\Users\10540\Desktop\琪乐无穷\CPLX2虚拟敲除_Cplx2VirtualKO"
for dirpath, _, files in os.walk(root):
    for n in files:
        fp = os.path.join(dirpath, n)
        print(os.path.getsize(fp), fp)
