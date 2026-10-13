import os
fig = r"C:\Users\10540\Desktop\琪乐无穷\CPLX2虚拟敲除_Cplx2VirtualKO\结果文件\图片文件"
for n in os.listdir(fig):
    if "Rplp0Network" in n:
        os.remove(os.path.join(fig, n))
        print("removed", n)
