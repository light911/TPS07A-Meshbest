import json,time
import pathlib
import base64
import numpy
import matplotlib.pyplot as plt
from scipy.ndimage import maximum_filter
from scipy.ndimage import generate_binary_structure, binary_erosion


def readfile(path:pathlib.Path):
    with open(path,'r') as f:
        data = json.load(f)
    try:
        temp = data['1']['data']
        # print(data['1']['data']['MeshBest'].keys())
    except KeyError:
        temp = data
        # print(data.keys())
   
    xnum = temp['grid_info']['steps_x']
    ynum = temp['grid_info']['steps_y']
    # print(xnum,ynum)
    Dtable = numpy.frombuffer(base64.b64decode(temp['MeshBest']['Dtable']))
    Dtable = numpy.reshape(Dtable, (ynum, xnum))
    # print(Dtable)
    return xnum,ynum,Dtable
def peaksearh(array2D):
    max = numpy.amax(array2D)

    pass
def gen_refarray(array:numpy.ndarray):
    # https://stackoverflow.com/questions/44230312/fastest-way-to-create-numpy-2d-array-of-indices
    m,n =array.shape
    r0 = numpy.arange(m) # Or r0,r1 = np.ogrid[:m,:n], out[:,:,0] = r0
    r1 = numpy.arange(n)
    out = numpy.empty((2,m,n),dtype=int)
    out[0:,:] = r0[:,None]
    out[1,:,:] = r1
    return out
def select_subset(array:numpy.ndarray,centerCoord,distance):
    # https://stackoverflow.com/questions/69856636/is-there-a-way-to-select-a-subset-of-a-numpy-2d-array-using-the-manhattan-distan
    t0 = time.time()
    # Asize=max(array.shape)
    # xarr = numpy.arange(Asize)
    # idxMat = gen_refarray(array)
    idxMat = array
    # print(idxMat)
    pt = numpy.array(centerCoord).reshape(-1,1,1)
    # print(pt)
    elems =  numpy.abs(idxMat-pt).sum(axis=0) <= distance   
    return elems

def detect_peaks_1(image:numpy.ndarray,threshold:float=1,distance:int=1,maxnum:int=200):
    t0=time.time()
    # max = numpy.amax(image)
    # print(max)
    # print(image.argmax())
    # data = numpy.copy(image)
    data = numpy.ma.array(image)
    posdata = numpy.ma.array(image)
    refarray = gen_refarray(data)
    peaks=[]
    while len(peaks) < maxnum: 
        # print(numpy.nanmax(data))
        if numpy.nanmax(data) > threshold:
            max_pos = numpy.unravel_index(numpy.nanargmax(data),data.shape)#(x,y)
            peaks.append(max_pos)
            newmask = select_subset(refarray,max_pos,distance)
            data = numpy.ma.masked_where(newmask,data)
            # numpy.ma.masked_where(newmask,data,copy=False)
            posdata[max_pos[0],max_pos[1]] = numpy.ma.masked
            
            
        else:
            break
    # print(len(peaks))
    
    # print(type(data.mask))
    print(f'detect_peaks_1:Run time = {time.time()-t0}')
    #peaks pos,mask for pos,debug map
    return peaks,posdata.mask,data.mask
    # while len(peaks) < maxnum: 
    #     print(numpy.nanmax(data))
    #     if numpy.nanmax(data) > threshold:
    #         max_pos = numpy.unravel_index(numpy.nanargmax(data),data.shape)#(x,y)
    #         peaks.append(max_pos)
    #         data[max_pos[0],max_pos[1]] = numpy.nan
            
    #     else:
    #         break
    # print(peaks)
    pass
def detect_peaks(image):
    """
    Takes an image and detect the peaks usingthe local maximum filter.
    Returns a boolean mask of the peaks (i.e. 1 when
    the pixel's value is the neighborhood maximum, 0 otherwise)
    """
    # https://stackoverflow.com/questions/3684484/peak-detection-in-a-2d-array

    t0 = time.time()
    # define an 8-connected neighborhood
    neighborhood = generate_binary_structure(2,2)
    # print(neighborhood)
    # [[ True  True  True]
    # [ True  True  True]
    # [ True  True  True]]

    #apply the local maximum filter; all pixel of maximal value 
    #in their neighborhood are set to 1
    local_max = maximum_filter(image, footprint=neighborhood) == image
    # print(maximum_filter(image, footprint=neighborhood))
    #local_max is a mask that contains the peaks we are 
    #looking for, but also the background.
    #In order to isolate the peaks we must remove the background from the mask.

    #we create the mask of the background
    background = (image==0)

    #a little technicality: we must erode the background in order to 
    #successfully subtract it form local_max, otherwise a line will 
    #appear along the background border (artifact of the local maximum filter)
    eroded_background = binary_erosion(background, structure=neighborhood, border_value=1)

    #we obtain the final mask, containing only peaks, 
    #by removing the background from the local_max mask (xor operation)
    detected_peaks = local_max ^ eroded_background
    print(f'detect_peaks :Run time = {time.time()-t0}')
    return detected_peaks

def plot(array2D):
    
    # plt.imshow(array2D, interpolation='none')
    # plt.show()


    
    detected_peaks = detect_peaks(array2D)
    peaks,detected_peaks_1,debug = detect_peaks_1(array2D)
    plt.subplot(1,4,(1))
    plt.imshow(array2D)
    plt.subplot(1,4,(2) )
    plt.imshow(detected_peaks)
    plt.subplot(1,4,(3) )
    plt.imshow(detected_peaks_1)
    plt.subplot(1,4,(4) )
    # print(debug,detected_peaks_1)
    plt.imshow(debug)
    plt.show()


if __name__ == '__main__':
    # x,y,Dtable = readfile("Z:\\Eddie\\Work\\viwe_1_result.json")
    # x,y,Dtable = readfile("/NAS/Eddie/Work/viwe_1_result.json")
    x,y,Dtable = readfile("/NAS/Eddie/Work/TPP1.json")
    # detected_peaks = detect_peaks(Dtable)
    # detect_peaks_1(Dtable)
    # print(detect_peaks(Dtable))
    plot(Dtable)
    pass