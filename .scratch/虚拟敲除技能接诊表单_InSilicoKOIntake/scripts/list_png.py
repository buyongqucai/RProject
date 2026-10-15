import os
fig = r"C:\Users\10540\Desktop\琪乐无穷\CPLX2虚拟敲除_Cplx2VirtualKO\结果文件\图片文件"
for n in sorted(os.listdir(fig)):
    if n.endswith(".png"):
        print(n)
