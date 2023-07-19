import h5py,cbf
import pathlib
import time,numpy


def readframe(path:pathlib.Path,framnums):
    with h5py.File(path,'r') as h5file:
        dataset = h5file['/entry/data/']
        # print(dataset.keys())#key just data_00001/data_000002
        # print(dataset.values())#this is datasets
        alldata = []
        for framnum in framnums:
            datasetpos = 0
            datalenindex = 0
            index = -1
            for data in dataset.values():
                datalenindex += data.shape[0]

                if (datalenindex-framnum) >= 0:
                    index = abs(datalenindex-framnum-data.shape[0]+1)
                    
                    locdata = data[index]
                    alldata.append(data[index])
                    break
                else:
                    # index += data.shape[0]
                    datasetpos += 1
                
            # print(datasetpos)
            # print(locdata[datasetpos])
            # print(type(locdata))
            # print(index,datasetpos)
        return alldata

if __name__ == "__main__":
    # readframe('/home/blctl/Desktop/NAS/Eddie/TPS07A/MeshbestServer/example/ins_1_0001_master.h5',2)
    t0 = time.time()
    # h5path= pathlib.Path('/home/blctl/Desktop/NAS/Eddie/TPS07A/MeshbestServer/example/01_X0_1_0001_master.h5')
    h5path= pathlib.Path('/NAS/Eddie/TPS07A/MeshbestServer/example/01_X0_1_0001_master.h5')
    frames = [1]
    alldata = readframe(h5path,frames)
    for data,frame in zip(alldata,frames):
        cbfpath = h5path.parent / f'{h5path.stem}_{frame:05d}.cbf'
        #this is for dozor which only take 32bit
        if data.dtype != "uint32" :
            if data.dtype == "uint16":
                maxV=65535
            elif data.dtype == "uint8":
                maxV=255
            else:
                maxV=4294967295
            data = data.astype('uint32')
            data = numpy.where(data==maxV,4294967295,data)
        print(cbfpath)
        cbf.write(cbfpath,data)
    print(f'Run time = {time.time()-t0}')