from model import HFSPGAInput
from Jobs import Job
from Machines import Machine_Time_window
import numpy as np
 
class Decode:
    def __init__(self, J, GAInput: HFSPGAInput, M_num):
        self.Processing_time = GAInput.ProcessingTime
        self.Machine_start_time = GAInput.MachineStartTime
        self.Time_efficent = GAInput.TimeEfficent
        self.Machine_buffer = GAInput.MachineBuffer
        self.GAInput = GAInput
        self.Scheduled = []  # 已经排产过的工序
        self.M_num = M_num
        self.Machines: list[Machine_Time_window] = []  # 存储机器类
        self.fitness = 0
        self.IsWorst = GAInput.IsWorst
        self.J=J            #
        for j in range(M_num):
            self.Machines.append(Machine_Time_window(j))
        self.Machine_State = np.zeros(M_num, dtype=int)  # 在机器上加工的工件是哪个
        self.Jobs: list[Job] = []     #存储工件类
        for k, v in J.items():
            self.Jobs.append(Job(k, v))
    #时间顺序矩阵和机器顺序矩阵
    def Order_Matrix(self,MS):
        JM=[]
        T=[]
        Ms_decompose=[]
        Site=0
        for S_i in self.J.values():
            Ms_decompose.append(MS[Site:Site+S_i])
            Site+=S_i
        for i in range(len(Ms_decompose)):
            JM_i=[]
            T_i=[]
            for j in range(len(Ms_decompose[i])):
                O_j=self.Processing_time[i][j]
                M_ij=[]
                T_ij=[]
                for Mac_num in range(len(O_j)):  # 寻找MS对应部分的机器时间和机器顺序
                    if O_j[Mac_num] is not None and len(O_j[Mac_num]) > 0:
                        M_ij.append(Mac_num)
                        T_ij.append(O_j[Mac_num])
                    else:
                        continue
                JM_i.append(M_ij[Ms_decompose[i][j]])
                T_i.append(T_ij[Ms_decompose[i][j]])
            JM.append(JM_i)
            T.append(T_i)
        return JM,T
    def Earliest_Start(self,Job: int,O_num,Machine: int,JM,Weight:int): # 计算工序的开始时间
        Selected_Machine=Machine
        #计算真正的机器（C1~C4必须在相同工位进行，包装工序要在对应的标定工位之后进行）
        index = self.Jobs[Job].Current_Processed()
        if index == 2 or index == 4: #装配2、接线
            Selected_Machine = self.Jobs[Job].J_machine[0] #在装配1工位进行
        elif index == 6: #包装工序
            Selected_Machine = self.Jobs[Job].J_machine[5] + 2 #所在标定工位+2即为包装工位
        machine_start = 0   # 本机器开工时间
        if (self.Machine_start_time is not None and len(self.Machine_start_time) > Selected_Machine):
            machine_start = self.Machine_start_time[Selected_Machine]
        last_O_end = self.Jobs[Job].Last_Processing_end_time  #本工件上道工序结束时间
        Next_Machine_start_time = self.Get_Job_Shift_Time(self.Machines[Selected_Machine],JM, last_O_end)   #本机器上一个工件的流转时刻
        ealiest_start = max(machine_start, last_O_end, Next_Machine_start_time)
        
        M_window = self.Machines[Selected_Machine].Empty_time_window()
        M_Tstart = M_window[0]
        M_Tend = M_window[1]
        M_Tlen = M_window[2]
        for le_i in range(len(M_Tlen)):# 此处为全插入时窗
            m_start = M_Tstart[le_i]
            m_end = M_Tend[le_i]
            if ealiest_start < m_start:
                ealiest_start = m_start
            if m_start <= ealiest_start and ealiest_start < m_end:
                if self.GAInput.MachineNeedWorker.__contains__(Selected_Machine):
                    #人工生产工序需求：
                    #工件进入工位后，需要判断是否有空余的工人进行加工，如没有，则需要等待
                    #标定1、2工位需要使用砝码，若标定工位现有砝码不同，则需要等待换型完成；若砝码已在其它标定工位使用，则需要等其结束再换型
                    if Selected_Machine == 6 or Selected_Machine == 7:
                        WeightName = self.GAInput.ProcessingWeight[Job][Weight]
                        Para = self.Get_Weight_Time(ealiest_start, Selected_Machine, WeightName, Job, O_num, m_end)
                    else:
                        Para = self.Get_C_Time(ealiest_start, Selected_Machine, Job, O_num, m_end)
                else:
                    #自动化工序
                    Para = self.GetEndByStart(ealiest_start, O_num, Selected_Machine, Job)
                if Para is None:
                    continue
                M_Ealiest = Para[0]
                P_t = Para[1]
                End_work_time = Para[2]
                if m_start <= M_Ealiest and End_work_time <= m_end: #可在该时窗内完成
                    return M_Ealiest, Selected_Machine, P_t, O_num,last_O_end,End_work_time
    #解码
    def Decode_1(self,CHS:list[int],Len_Chromo):
        MS=list(CHS[0:Len_Chromo])
        OS=list(CHS[Len_Chromo:2*Len_Chromo])
        WS=list(CHS[2*Len_Chromo:2*Len_Chromo+len(self.Jobs)])
        Needed_Matrix=self.Order_Matrix(MS)
        JM=Needed_Matrix[0]
        for i in OS:
            Job=i
            O_num=self.Jobs[Job].Current_Processed()
            Machine: int=JM[Job][O_num]
            weight = WS[i]
            Para=self.Earliest_Start(Job, O_num, Machine, JM, weight)
            self.Jobs[Job]._Input(Para[0],Para[5],Para[1])
            if Para[5] > self.fitness:
                self.fitness = Para[5]
            self.Machines[Para[1]]._Input(Job, Para[0], Para[5], Para[2], Para[3], weight)
        return self.fitness if self.IsWorst is False else 1 / self.fitness
    #根据工序开始时间计算结束时间
    def GetEndByStart(self, ealiest_start, O_num, Machine, Job):
        M_Ealiest = ealiest_start # 加工开始时间
        End_work_time = M_Ealiest # 计算跳过休息时间的加工结束时间
        rest_work = 1 # 剩余加工进度，初始100%
        P_t = 0 # 总加工时间
        # P_t=self.Processing_time[Job][O_num][Machine]
        for i in range(len(self.Time_efficent)):
            start = self.Time_efficent[i] # 开始时间
            end = 9999 # 结束时间
            if i + 1 < len(self.Time_efficent):
                end = self.Time_efficent[i + 1]
            efficent = self.Processing_time[Job][O_num][Machine][i] # 根据能效获取节拍
            if end < M_Ealiest:
                continue
            if start <= M_Ealiest and end > M_Ealiest:
                # 找到了开工时间
                if efficent == -1:
                    # 最早开工时间落在了休息时间，往后顺延
                    M_Ealiest = end
                    End_work_time = end
                    continue
            if End_work_time < end:
                if efficent == -1:
                    # 休息时间，结束时间累加
                    End_work_time = end
                else:
                    # 计算结束时间
                    if end - End_work_time >= efficent * rest_work:
                        # 时间段内能做完
                        End_work_time += efficent * rest_work
                        P_t += efficent * rest_work
                        break
                    else:
                        # 不能做完，计算完成度
                        rest_work -= (end - End_work_time) / efficent
                        P_t += end - End_work_time
                        End_work_time = end
        return M_Ealiest, P_t, End_work_time
    #计算流转时间
    def Get_Job_Shift_Time(self, machine: Machine_Time_window,JM: list[list[int]], current_O_start: int):
        #也就是本机器上一个工件的下一道工序所在机器的开始时间(流转时刻)
        #获取本机器上一个工件
        if len(machine.assigned_task) == 0:
            return 0
        if current_O_start > 0:
            last_task = None
            for i in range(len(machine.assigned_task)):
                if machine.O_end[-1-i] <= current_O_start:
                    #最后一个结束时间小于指定时间的工件
                    last_task = machine.assigned_task[-1-i]
                    last_o_end = machine.O_end[-1-i]
                    last_job = self.Jobs[last_task[0] - 1]
                    last_o = last_task[1]
                    break
            if last_task is None:
                #机器没有早于该时间加工的工件
                return 0
        else:
            last_task = machine.assigned_task[-1]
            last_o_end = machine.O_end[-1]
            last_job = self.Jobs[last_task[0] - 1]
            last_o = last_task[1]
        if last_job.Operation_num > last_o + 1:
            #还有未完成的工序
            next_o_machine_index = JM[last_task[0] - 1][last_task[1]]
            if last_o == 2 or last_o == 4: #下一道是装配2、接线
                next_o_machine_index = last_job.J_machine[0] #在装配1工位进行
            elif last_o == 6: #下一道包装工序
                next_o_machine_index = last_job.J_machine[5] + 2 #所在标定工位+2即为包装工位
            next_o_machine = self.Machines[next_o_machine_index]
            #判断下一个机器是否有buffer
            next_o_machine_has_buffer = False
            if self.Machine_buffer is not None:
                for i in self.Machine_buffer:
                    if i ==  next_o_machine_index:
                        next_o_machine_has_buffer = True
                        break
            if next_o_machine_has_buffer:
                #下一个机器有buffer
                return last_o_end
            else:
                #由于下一个机器也会有加工的工件，而其流转时刻又受下下个机器影响，所以需要计算
                next_machine_time = 0
                if len(next_o_machine.assigned_task) > 0 and next_o_machine.assigned_task.__contains__([last_task[0], last_task[1] + 1]):
                    next_machine_time = next_o_machine.O_start[next_o_machine.assigned_task.index([last_task[0], last_task[1] + 1])]
                return max(last_o_end, next_machine_time)
        else:
            #工件所有工序加工完成，返回加工完成时间
            return last_o_end
    #获取首个工人可用时间
    def Get_C_Time(self, startTime: int, machine: int, Job: int, O_num: int, lastest_end: int):
        CWorkerCount = self.GAInput.ResourceConfig["CWorkerCount"]
        # 先计算在startTime时刻，有多少个正在加工的工件
        while True:
            para = self.GetEndByStart(startTime, O_num, machine, Job)
            if para[2] > lastest_end:
                return None
            conflict = False
            for m in range(para[0], para[2]):
                # 每一分钟都进行判断 
                CJobCount = 1   # 本工件也需要加工
                for i in self.GAInput.MachineNeedWorker:
                    if machine == i:
                        continue
                    otherMachine = self.Machines[i]
                    #便利机器上所有的加工记录
                    for j in range(len(otherMachine.assigned_task)):
                        o_start = otherMachine.O_start[j]
                        o_end = otherMachine.O_end[j]
                        if o_start <= m and m <= o_end:
                            #如果时间有交集，则工人数量加1
                            CJobCount += 1
                            break
                if CJobCount > CWorkerCount:
                    conflict = True
                    break
            if conflict:
                #继续运算
                startTime = para[0] + 1
            else:
                return para
    #获取标定可用时间
    def Get_Weight_Time(self, ealiest_start: int, machine: int, weightName: str, Job: int, O_num: int, lastest_end: int):
        resourceTime = ealiest_start
        CWorkerCount = self.GAInput.ResourceConfig['CWorkerCount']
        Weight1TCount = self.GAInput.ResourceConfig["1T"]
        Weight2TCount = self.GAInput.ResourceConfig["2T"]
        Weight3TCount = self.GAInput.ResourceConfig["3T"]
        #本标定产线
        self_machine = self.Machines[machine]
        self_last_end = 0
        lastWeight = ''
        if len(self_machine.O_end) > 0:
            self_last_end = self_machine.O_end[-1]
            lastWeightIndex = self_machine.worker_for_task[-1]
            lastJobIndex = self_machine.assigned_task[-1][0] - 1
            lastWeight = self.GAInput.ProcessingWeight[lastJobIndex][lastWeightIndex]
        if weightName != lastWeight:
            #增加五分钟换型
            resourceTime = max(self_last_end + self.GAInput.WeightExchangeTime, ealiest_start)
        Weight1TUsedCount = 0
        Weight2TUsedCount = 0
        Weight3TUsedCount = 0
        #所用砝码
        if weightName == '1T':
            Weight1TUsedCount += 1
        elif weightName ==  '2T':
            Weight2TUsedCount += 1
        elif weightName ==  '3T':
            Weight3TUsedCount += 1
        elif weightName ==  '6T':
            Weight3TUsedCount += 2
        #其它标定产线
        other_machines = [6, 7]
        other_machines.remove(machine)
        while True:
            #计算加工前5分钟到加工后5分钟内，其它标定产线是否有砝码冲突
            end_time = self.GetEndByStart(resourceTime, O_num, machine, Job)
            #判断是否满足时间窗口要求
            if end_time[2] > lastest_end:
                return None
            judge_start = end_time[0] - self.GAInput.WeightExchangeTime if end_time[0] - self.GAInput.WeightExchangeTime > 0 else 0
            judge_end = end_time[2] + self.GAInput.WeightExchangeTime
            #计算这段时间内，其它标定产线使用的砝码是否存在冲突
            conflict = False
            for m in range(judge_start + 1, judge_end):
                #判断第m分钟砝码是否有冲突
                Weight1TUsingCount = 0
                Weight2TUsingCount = 0
                Weight3TUsingCount = 0
                for other_machine_index in other_machines:
                    #遍历所有其它标定工位
                    other_machine = self.Machines[other_machine_index]
                    if len(other_machine.assigned_task) == 0:
                        continue
                    for i in range(len(other_machine.assigned_task)):
                        o_start = other_machine.O_start[i]
                        o_end = other_machine.O_end[i]
                        if o_start > m or o_end < m:
                            continue
                        #时间有交集，增加相应砝码
                        lastWeightIndex = other_machine.worker_for_task[i]
                        lastJobIndex = other_machine.assigned_task[i][0] - 1
                        lastWeight = self.GAInput.ProcessingWeight[lastJobIndex][lastWeightIndex]
                        if lastWeight == '1T':
                            Weight1TUsingCount += 1
                        elif lastWeight ==  '2T':
                            Weight2TUsingCount += 1
                        elif lastWeight ==  '3T':
                            Weight3TUsingCount += 1
                        elif lastWeight ==  '6T':
                            Weight3TUsingCount += 2
                        break
                if Weight1TUsingCount + Weight1TUsedCount > Weight1TCount or Weight2TUsingCount + Weight2TUsedCount > Weight2TCount or Weight3TUsingCount + Weight3TUsedCount > Weight3TCount:
                    #砝码冲突
                    conflict = True
                    break
                #判断第m分钟工人数量是否冲突
                CJobCount = 1   # 本工件也需要加工
                for i in self.GAInput.MachineNeedWorker:
                    if machine == i:
                        continue
                    otherMachine = self.Machines[i]
                    #便利机器上所有的加工记录
                    for j in range(len(otherMachine.assigned_task)):
                        o_start = otherMachine.O_start[j]
                        o_end = otherMachine.O_end[j]
                        if o_start <= m and m <= o_end:
                            #如果时间有交集，则工人数量加1
                            CJobCount += 1
                            break
                if CJobCount > CWorkerCount:
                    conflict = True
                    break
            if conflict:
                #不满足，继续
                resourceTime = end_time[0] + 1
                continue
            else:
                #无冲突
                break
        return end_time