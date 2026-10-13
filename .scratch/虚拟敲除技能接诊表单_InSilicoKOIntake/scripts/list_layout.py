import os
root = r"C:\Users\10540\Desktop\琪乐无穷\CPLX2虚拟敲除_Cplx2VirtualKO"
for name in os.listdir(root):
    print("TOP", name)
    p = os.path.join(root, name)
    if os.path.isdir(p):
        for n2 in os.listdir(p):
            print(" ", n2)
