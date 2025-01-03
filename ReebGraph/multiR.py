import numpy as np
import math
import os
import multiprocessing as mp
from tqdm import tqdm

class Trajectory:
    def __init__(self, points, tid, segments=None):
        self.points = points
        self.tid = tid
        self.segments = segments

class Segment:
    def __init__(self, p1, p2, segid, bid=None, e_seg=None):
        self.p1 = p1
        self.p2 = p2
        self.segid = segid
        self.bid = bid
        self.e_seg = e_seg

class Image:
    def __init__(self, trajectories):
        self.trajectories = trajectories

class Bundle:
    def __init__(self, segments, bid):
        self.segments = segments
        self.bid = bid

class Event:
    def __init__(self, event, trajectory1=None, trajectory2=None, t1=None, t2=None, considered=False):
        self.event = event
        self.trajectory1 = trajectory1
        self.trajectory2 = trajectory2
        self.t1 = t1
        self.t2 = t2
        self.considered = considered

class GNode:
    def __init__(self, trajectory):
        self.trajectory = trajectory

class RNode:
    def __init__(self, traj_list, index_list):
        self.traj_list = traj_list
        self.index_list = index_list

def create_image(streamlines, eps=4):
    image = []
    for i in range(len(streamlines)):
        T = streamlines[i]
        segments_T = []
        for j in range(len(T) - 1):
            segments_T.append(Segment(T[j], T[j + 1], str(i) + "_" + str(j)))
        image.append(Trajectory(T, str(i), segments_T))
    I = Image(image)
    return I

num_cores = mp.cpu_count()

def my_function(t, I, s, eps):
    T1 = I.trajectories[s]
    T2 = I.trajectories[t]
    connectEventList, disconnectEventList = findConnectDisconnectEvents(T1, T2, eps)
    return (connectEventList, disconnectEventList)

def create_trajectory_dic(I, eps):
    dic_T = {}
    for s in range(len(I.trajectories)):
        T1 = I.trajectories[s]
        dic_T[s] = {}
        k1 = 0
        e1 = Event("appear", s)
        dic_T[s][k1] = [e1]
        k2 = len(T1.points) - 1
        e2 = Event("disappear", s)
        dic_T[s][k2] = [e2]

    for s in range(len(I.trajectories)):
        myList = [i for i in range(s + 1, len(I.trajectories))]
        inputs = tqdm(myList)
        pool = mp.Pool(processes=num_cores)
        processed_list = pool.starmap(my_function, [(t, I, s, eps) for t in myList])
        pool.close()

        for i, result in enumerate(processed_list):
            connectEventList, disconnectEventList = result
            t = myList[i]
            for c in connectEventList:
                e = Event("connect", s, t, c[0], c[1])
                dic_T[s].setdefault(c[0], []).append(e)
                dic_T[t].setdefault(c[1], []).append(e)
            for c in disconnectEventList:
                e = Event("disconnect", s, t, c[0], c[1])
                dic_T[s].setdefault(c[0], []).append(e)
                dic_T[t].setdefault(c[1], []).append(e)
    return dic_T

def check_seg_e_connected(s1, s2, eps):
    d1 = math.sqrt(((s1.p1[0] - s2.p1[0]) ** 2) + ((s1.p1[1] - s2.p1[1]) ** 2) + ((s1.p1[2] - s2.p1[2]) ** 2))
    d2 = math.sqrt(((s1.p2[0] - s2.p2[0]) ** 2) + ((s1.p2[1] - s2.p2[1]) ** 2) + ((s1.p2[2] - s2.p2[2]) ** 2))
    return max(d1, d2) < eps

def checkEpsilonDistance(p1, p2, eps):
    return (np.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2 + (p1[2] - p2[2]) ** 2)) < eps

def findConnectDisconnectEvents(T1, T2, eps):
    connectedEventsList = []
    disconnectedEventsList = []
    i = 0
    i_start = len(T1.points)
    j_start = len(T2.points)
    while i < len(T1.points):
        j = 0
        while j < len(T2.points):
            if checkEpsilonDistance(T1.points[i], T2.points[j], eps):
                i_start = i
                j_start = j
                i = len(T1.points)
                break
            j += 1
        i += 1

    i, j = i_start, j_start
    prev = ""
    while i < len(T1.points) and j < len(T2.points):
        if checkEpsilonDistance(T1.points[i], T2.points[j], eps):
            if prev != "C":
                connectedEventsList.append([i, j])
                prev = "C"
        else:
            if prev != "D":
                disconnectedEventsList.append([i, j])
                prev = "D"
        i += 1
        j += 1

    return connectedEventsList, disconnectedEventsList
