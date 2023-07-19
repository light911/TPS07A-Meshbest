import h5py
import bitshuffle.h5
import pathlib
import time
import os,time,re,signal,argparse,sys,math,shutil,numpy


def mergeframe(path:pathlib.Path,framnums:int):
    #copy master file
    print(path.stem)
    newname = path.stem.replace("_master", f'_merge_{framnums}_frame_master') + '.h5'
    # print(newname)
    newpath = path.with_name(newname)
    shutil.copy(path, newpath)
    
    with h5py.File(newpath,'r+') as h5file:
        numberimage = int(h5file['/entry/instrument/detector/detectorSpecific/nimages'][()])
        exptime = h5file['/entry/instrument/detector/frame_time'][()]
        framewidth = h5file['/entry/sample/transformations/omega_range_average'][()]
        StartOmega = h5file['/entry/sample/transformations/omega'][()][0]
        StartOmegaall = h5file['/entry/sample/transformations/omega'][()]
        print(StartOmegaall)
        print(StartOmega)
        print(numberimage)
        print(len(StartOmegaall))
        


        olddataset = h5file['/entry/data/']

        

        framenumaftermerge = math.floor(numberimage/framnums)
        index = 0
        block_size =0
        # print(list(olddataset.values())[0].shape)
        nimage_dataset,xnum,ynum = list(olddataset.values())[0].shape
        # print(nimage_dataset,xnum,ynum)
        print(list(olddataset.values())[0])
        totaldataset=math.ceil(framenumaftermerge / nimage_dataset)
        print(f'{totaldataset=},{framenumaftermerge=}')

        
        #upate header
        h5file['/entry/instrument/detector/detectorSpecific/nimages'][()] = framenumaftermerge
        h5file['/entry/instrument/detector/frame_time'][()] = exptime*framnums
        h5file['/entry/instrument/detector/count_time'][()] = exptime*framnums

        h5file['/entry/sample/transformations/omega_range_average'][()] = framewidth * framnums
        h5file['/entry/sample/goniometer/omega_range_average'][()] = framewidth * framnums

        
        omgeaarray =numpy.arange(StartOmega,framewidth * framnums*framenumaftermerge,framewidth * framnums)
        # h5file['/entry/sample/transformations/omega'][...]=omgeaarray
        tempattrs={}
        tempattrs.update(h5file['/entry/sample/transformations/omega'].attrs)
        # print(h5file['/entry/sample/transformations/omega'].attrs.items())
        print(tempattrs)

        
        del h5file['/entry/sample/transformations/omega']
        h5file.create_dataset("/entry/sample/transformations/omega", (1, len(omgeaarray)))
        h5file['/entry/sample/transformations/omega'][()] = omgeaarray
        for item in tempattrs:
            # print(item)
            h5file['/entry/sample/transformations/omega'].attrs.create(item, tempattrs[item])

        tempattrs={}
        tempattrs.update(h5file['entry/data/'].attrs)
        # print(h5file['/entry/sample/transformations/omega'].attrs.items())
        print(tempattrs)

        # del h5file['/entry/data/']
        # h5file.create_group('/entry/data/')
        # for item in tempattrs:
        #     # print(item)
        #     h5file['/entry/data/'].attrs.create(item, tempattrs[item])
        

        newdatasetlist = []
        finaldatalist = []
        for i in range(1,totaldataset+1):
            name = newpath.stem.replace("_master", f'_data_{i:06d}') + '.h5'
            f = h5py.File(path.with_name(name), "w")
            maxdatasetindex,maxnewframeindex = get_data_pos_index(nimage_dataset,framenumaftermerge)
            if maxdatasetindex+1 == i:
                #last file
                num_frame = maxnewframeindex+1
                low = (i-1)*nimage_dataset +1
                high = (i-1)*nimage_dataset + (maxnewframeindex+1)
            else:
                num_frame = nimage_dataset
                low = (i-1)*nimage_dataset +1
                high = (i)*nimage_dataset 

            print(f'{maxdatasetindex=},{i=},{num_frame=}')
            dataset = f.create_dataset(
            "/entry/data/data",
            (num_frame, xnum, ynum),
            compression=bitshuffle.h5.H5FILTER,
            compression_opts=(block_size, bitshuffle.h5.H5_COMPRESS_LZ4),
            dtype='<u4',
            chunks=(1,xnum,ynum),
            maxshape=(None, xnum,ynum)
            )
            
            dataset.attrs.create("image_nr_low",low,dtype='<u8')
            dataset.attrs.create("image_nr_high", high,dtype='<u8')
            
            a = numpy.zeros((num_frame,xnum,ynum),dtype=numpy.uint32)
            finaldatalist.append(a)
            newdatasetlist.append(f)
        print(newdatasetlist)

        # write to file
        t0=time.time()
        for i in range(1,framenumaftermerge+1):
            #load data
            t0=time.time()
            tempfor_merge = numpy.zeros((xnum,ynum),dtype=numpy.uint32)
            # print(tempfor_merge)
            for data in range(1,framnums+1):
                print(i,data,data+(i-1)*framnums)# current merge frame, subset index(1,2,3,4), index in old dataset
                readimage = data+(i-1)*framnums
                #find position in old dataset
                datasetindex,oldframeindex = get_data_pos_index(nimage_dataset,readimage)
                # print(f'{datasetindex},{newframeindex}')
                # print(list(datasetnamelist[datasetindex])[newframeindex])
                # tempfor_merge += list(olddataset.values())[datasetindex][oldframeindex]
                tempfor_merge = non_overflowing_sum(tempfor_merge,list(olddataset.values())[datasetindex][oldframeindex])
                # print(f'{tempfor_merge.max()=},{list(olddataset.values())[datasetindex][oldframeindex].max()=}')
                
                pass
                # load
            #write for newframe
            #find position in new dataset
            newdatasetindex,newframeindex = get_data_pos_index(nimage_dataset,i)
            print(f'write for newframe')
            print(f'{newdatasetindex=},{newframeindex=}')
            # print(newdatasetlist[newdatasetindex].values())#ValuesViewHDF5(<HDF5 file "01_X0_1_0001_merge_4_frame_data_000001.h5" (mode r+)>)
            
            # print(list(newdatasetlist[newdatasetindex].values())[0]["/data/entry/data"])#<HDF5 dataset "data": shape (900, 4362, 4148), type "<f4">
            t1 =time.time()
            print(f'Read frame take {t1-t0} sec')
            # list(newdatasetlist[newdatasetindex].values())[0]["/data/entry/data"][newframeindex,...] = tempfor_merge
            finaldatalist[newdatasetindex][newframeindex] = tempfor_merge
            print(f'Write to mem take {time.time()-t1} sec')
            # exit()
            # newdatasetlist[newdatasetindex][newframeindex,...] = tempfor_merge
            # newdatasetlist[newdatasetindex][newframeindex] = tempfor_merge
            print(f'Merge frame take {time.time()-t0} sec')
            pass
        #write to file
        t2 = time.time()
        for dataset,data in zip(newdatasetlist,finaldatalist):
            list(dataset.values())[0]["/entry/data/data"][:] = data
            pass
        print(f'Write to disk take {time.time()-t2} sec')    
        for f in newdatasetlist:
            f.close()

        for item in h5file['/entry/data/'].keys():
            print(f'del {item}')
            del h5file['/entry/data/'][item]
        for i in range(totaldataset):
            name = newpath.stem.replace("_master", f'_data_{i+1:06d}') + '.h5'
            print(name)
            h5file[f'/entry/data/data_{i+1:06d}'] =  h5py.ExternalLink(name, f'/entry/data/data')


        # pass
    pass
def get_data_pos_index(nimage_dataset,imagen):
    #imagen start form 1
    datasetindex,newframeindex = divmod(imagen,nimage_dataset)
    newframeindex += -1
    if newframeindex == -1:
        datasetindex += -1
        newframeindex = nimage_dataset - 1
    # datasetindex = math.floor(imagen/nimage_dataset)
    # newframeindex = imagen - datasetindex*nimage_dataset
    # print(datasetindex,newframeindex)
    return datasetindex,newframeindex
def non_overflowing_sum(a, b):
    #a,b is uint32
    # c = numpy.uint64(a)+b
    # c[numpy.where(c>4294967295)] = 4294967295
    a+=b; a[a<b]=4294967295
    return a
    # return numpy.uint32( c )


if __name__ == "__main__":
    t0=time.time()
    # signal.signal(signal.SIGINT, quit)
    # signal.signal(signal.SIGTERM, quit)
    path = pathlib.Path('/mnt/data_buffer/01_X0_1_0001_master.h5')
    # path = pathlib.Path('/mnt/data_buffer/test.h5')
    # path = pathlib.Path('/data/blctl/hdf5test/autostrago/test_p2_0_0010_master.h5')
    # path = pathlib.Path('/data/blctl/20211029_07A_multi_crystal/163451_collect/collect/002_0000_master.h5')
    
    # path = pathlib.Path('/data/blctl/20210824_07A_Exp/ins1/01_1_0001_master.h5')
    # path = pathlib.Path('/data/blctl/20210824_07A_Exp/ins1/02_2_0001_master.h5')
    # path = pathlib.Path('/data/blctl/20210824_07A_Exp/ins1/03_3_0001_master.h5')
    # path = pathlib.Path('/data/blctl/20210805_07A_Ligand_Search/lys01/lys01_1_0001_master.h5')
    par = argparse.ArgumentParser()
    #for test
    par.add_argument("file",type=pathlib.Path,help="master file path",nargs='?',default=path)
    # par.add_argument("file",type=pathlib.Path,help="master file path")
    
    par.add_argument("-frame",type=int,help="Number of frame for merge")
    par.add_argument("-showinfo",help="showheader",action='store_true')

    args=par.parse_args()
    # if args.showinfo:
    #     pass
    # else:
    if args.frame:
        framenum = args.frame
    else:
        framenum = 4
    if args.file:
        path = args.file
        
    mergeframe(path,framenum)      
    pass