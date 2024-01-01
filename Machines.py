class Machine_Time_window:
    def __init__(self,Machine_index):
        self.Machine_index=Machine_index
        self.assigned_task: list[list[int]] = []
        self.worker_for_task:list[str]=[]
        self.O_start:list[int] = []
        self.O_end:list[int] = []
        self.O_processing = []
        self.End_time=0
 
    #机器的哪些时间窗是空的,此处只考虑内部封闭的时间窗
    def Empty_time_window(self):
        time_window_start = []
        time_window_end = []
        len_time_window=[]
        if self.O_end is None:
            pass
        elif len(self.O_end)==1:
            if self.O_start[0]!=0:
                time_window_start=[0]
                time_window_end=[self.O_start[0]]
        elif len(self.O_end)>1:
            if self.O_start[0] !=0:
                time_window_start.append(0)
                time_window_end.append(self.O_start[0])
            time_window_start.extend(self.O_end[:-1])        #因为使用时间窗的结束点就是空时间窗的开始点
            time_window_end.extend(self.O_start[1:])
        if time_window_end is not None:
            len_time_window=[time_window_end[i]-time_window_start[i]  for i in range(len(time_window_end))]
        return time_window_start,time_window_end,len_time_window
 
    def Machine_Burden(self):
        if len(self.O_start)==0:
            burden=0
        else:
            processing_time=[self.O_end[i]-self.O_start[i] for i in range(len(self.O_start))]
            burden=sum(processing_time)
        return burden
 
    def _Input(self,Job,M_Ealiest,End_work_time,Processing_time,O_num, worker):
        if self.O_end!=[]:
            if self.O_start[-1]>M_Ealiest:
                for i in range(len(self.O_end)):
                    if self.O_start[i]>=M_Ealiest:
                        self.assigned_task.insert(i,[Job + 1, O_num + 1])
                        break
            else:
                self.assigned_task.append([Job+1,O_num+1])
        else:
            self.assigned_task.append([Job+1,O_num+1])
        self.O_start.append(M_Ealiest)
        self.O_end.append(End_work_time)
        self.O_processing.append(Processing_time)
        self.End_time=self.O_end[-1]
        self.worker_for_task.append(worker)