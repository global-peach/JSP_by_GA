from concurrent.futures import ALL_COMPLETED, Future, ThreadPoolExecutor, wait
import numpy as np
import random
from Decode_for_JSP import Decode
from Encode_for_JSP import Encode
import itertools

from model import HFSPGAInput


class JSPGAResult:
    def __init__(self, decode: Decode, best_fit: list, worst_fit: list, avg_fit: list, Optimal_CHS: list, Len_Chromo: int) -> None:
        self.Decode = decode
        self.BestFit = best_fit
        self.WorstFit = worst_fit
        self.AvgFit = avg_fit
        self.OptimalCHS = Optimal_CHS
        self.LenChromo = Len_Chromo

class GA:
    def __init__(self):
        self.Pop_size=100       #种群数量
        self.P_c=0.8            #交叉概率
        self.P_m=0.5            #变异概率
        self.P_v=0.5           #选择何种方式进行交叉
        self.P_w=0.95            #采用何种方式进行变异
        self.Max_Itertions=200  #最大迭代次数
        self.executor=ThreadPoolExecutor(max_workers=20)

    def calcFitness(self, J, GAInput, M_num, CHS, Len):
        d = Decode(J, GAInput, M_num)
        return d.Decode_1(CHS,Len)

    #适应度
    def fitness(self, CHS,J,GAInput: HFSPGAInput,M_num,Len):
        Fit=[]
        futures: list[Future] = []
        for i in range(len(CHS)):
            Fit.append(9999)
            future=self.executor.submit(self.calcFitness, J, GAInput, M_num, CHS[i], Len)
            futures.append(future)
        #wait(futures, return_when=ALL_COMPLETED)
        for i in range(len(futures)):
            Fit[i] = futures[i].result()
        return Fit
 
    #机器部分交叉
    def Crossover_Machine(self,CHS1,CHS2,T0,J_num):
        T_r=[j for j in range(T0)]
        r = random.randint(1, 10)  # 在区间[1,T0]内产生一个整数r
        random.shuffle(T_r)
        R = T_r[0:r]  # 按照随机数r产生r个互不相等的整数
        # 将父代的染色体复制到子代中去，保持他们的顺序和位置
        OS_1=CHS1[T0:2*T0]
        OS_2 = CHS2[T0:2 * T0]
        C_1 = CHS2[0:T0]
        C_2 = CHS1[0:T0]
        W_1 = CHS1[2*T0:2*T0 + J_num]
        W_2 = CHS2[2*T0:2*T0 + J_num]
        for i in R:
            K,K_2 = C_1[i],C_2[i]
            C_1[i],C_2[i] = K_2,K
        CHS1=np.hstack((C_1,OS_1, W_1))
        CHS2 = np.hstack((C_2, OS_2, W_2))
        return CHS1,CHS2
 
    #工序交叉部分
    def Crossover_Operation(self,CHS1, CHS2, T0, J_num, Processing_group):
        OS_1 = CHS1[T0:2 * T0]
        OS_2 = CHS2[T0:2 * T0]
        MS_1 =CHS1[0:T0]
        MS_2 = CHS2[0:T0]
        W_1 = CHS1[2*T0:2*T0 + J_num]
        W_2 = CHS2[2*T0:2*T0 + J_num]
        Set1 = []
        Set2 = []
        if (Processing_group is not None and len(Processing_group) > 0):
            #工件组合（加工顺序必须固定）
            if len(Processing_group) == 1 and len(Processing_group[0]) == J_num:
                return CHS1, CHS2
            Job_list = [i for i in range(J_num)]
            random.shuffle(Job_list)
            tmp_group = []
            for group in Processing_group:
                if (len(group) > 0):
                    tmp_group.append(group)
                    for i in group:
                        Job_list.remove(i)
            for i in Job_list:
                tmp_group.append([i])
            random.shuffle(tmp_group)
            r = random.randint(1, len(tmp_group) - 1)
            for group in tmp_group[0:r]:
                for i in group:
                    Set1.append(i)
            for group in tmp_group[r:len(tmp_group)]:
                for i in group:
                    Set2.append(i)
        else:
            Job_list = [i for i in range(J_num)]
            random.shuffle(Job_list)
            r = random.randint(1, J_num - 1)
            Set1 = Job_list[0:r]
            Set2 = Job_list[r:J_num]
        new_os1 = []
        new_os2 = []
        for i in OS_1:
            if i in Set1:
                new_os1.append(i)
            if i in Set2:
                new_os2.append(i)
        for i in OS_2:
            if i not in Set1:
                new_os1.append(i)
            if i not in Set2:
                new_os2.append(i)
        CHS1=np.hstack((MS_1,new_os1, W_1))
        CHS2 = np.hstack((MS_2, new_os2, W_2))
        return CHS1,CHS2
    #砝码交叉
    def Crossover_Weight(self, CHS1, CHS2, T0, J_num):
        T_r=[j for j in range(J_num)]
        r = random.randint(1, 10 if J_num > 10 else J_num)  # 在区间[1,T0]内产生一个整数r
        random.shuffle(T_r)
        R = T_r[0:r]  # 按照随机数r产生r个互不相等的整数
        # 将父代的染色体复制到子代中去，保持他们的顺序和位置
        OS_1=CHS1[T0:2*T0]
        OS_2 = CHS2[T0:2 * T0]
        C_1 = CHS2[0:T0]
        C_2 = CHS1[0:T0]
        W_1 = CHS1[2*T0:2*T0 + J_num]
        W_2 = CHS2[2*T0:2*T0 + J_num]
        for i in R:
            K,K_2 = W_1[i],W_2[i]
            W_1[i],W_2[i] = K_2,K
        CHS1=np.hstack((C_1,OS_1, W_1))
        CHS2 = np.hstack((C_2, OS_2, W_2))
        return CHS1,CHS2
 
    def reduction(self,num,J,T0):
        T0=[j for j in range(T0)]
        K=[]
        Site=0
        for k,v in J.items():
            K.append(T0[Site:Site+v])
            Site+=v
        for i in range(len(K)):
            if num in K[i]:
                Job=i
                O_num=K[i].index(num)
                break
        return Job,O_num
 
    #机器变异部分
    def Variation_Machine(self,CHS,O,T0,J, J_num):
        Tr=[i_num for i_num in range(T0)]
        MS=CHS[0:T0]
        OS=CHS[T0:2*T0]
        WS=CHS[2*T0:2*T0 + J_num]
        # 机器选择部分
        r = random.randint(1, T0 - 1)  # 在变异染色体中选择r个位置
        random.shuffle(Tr)
        T_r = Tr[0:r]
        for i in T_r:
            Job=self.reduction(i,J,T0)
            O_i=Job[0]
            O_j =Job[1]
            Machine_using = O[O_i][O_j]
            Machine_time = []
            for j in Machine_using:
                if j is not None and len(j) > 0:
                    Machine_time.append(j)
            Min_index = Machine_time.index(min(Machine_time))
            MS[i] = Min_index
        CHS=np.hstack((MS,OS,WS))
        return CHS
    #工序变异部分
    def Variation_Operation(self, CHS,T0,J_num,J,GAInput: HFSPGAInput,M_num):
        MS=CHS[0:T0]
        OS=list(CHS[T0:2*T0])
        WS=CHS[2*T0:2*T0 + J_num]
        r=random.randint(1,J_num-1)
        if r > 5:   #防止阶乘爆炸
            r = 5
        Tr=[i for i in range(J_num)]
        random.shuffle(Tr)
        Tr=Tr[0:r]
        J_os=dict(enumerate(OS))    #随机选择r个不同的基因
        J_os = sorted(J_os.items(), key=lambda d: d[1])
        Site=[]
        for i in range(r):
            Site.append(OS.index(Tr[i]))
        A=list(itertools.permutations(Tr, r))
        A_CHS=[]
        for i in range(len(A)):
            for j in range(len(A[i])):
                OS[Site[j]]=A[i][j]
            C_I=np.hstack((MS,OS,WS))
            A_CHS.append(C_I)
        Fit= self.fitness(A_CHS, J, GAInput, M_num, T0)
        return A_CHS[Fit.index(min(Fit))]
    #砝码变异
    def Variation_Weight(self, CHS,T0,J_num,J,GAInput: HFSPGAInput, M_num):
        MS=CHS[0:T0]
        OS=list(CHS[T0:2*T0])
        WS=CHS[2*T0:2*T0 + J_num]
        randomNum: list[int] = []
        A_CHS=[]
        for i in range(len(GAInput.ProcessingWeight)):
            if len(GAInput.ProcessingWeight[i]) > 1:
                randomNum.append(i)
        if len(randomNum) == 0:
            return CHS
        count = 0
        while len(randomNum) > 0 and count < 8:
            JobIndex = random.choice(randomNum)
            randomNum.remove(JobIndex)
            count += 1
            for i in range(len(GAInput.ProcessingWeight[JobIndex])):
                WS[JobIndex] = i
                C_I=np.hstack((MS,OS,WS))
                A_CHS.append(C_I)
        Fit= self.fitness(A_CHS, J, GAInput, M_num, T0)
        return A_CHS[Fit.index(min(Fit))]
    
    def Select(self,Fit_value):
        Fit=[]
        for i in range(len(Fit_value)):
            fit=1/Fit_value[i]
            Fit.append(fit)
        Fit=np.array(Fit)
        idx = np.random.choice(np.arange(len(Fit_value)), size=len(Fit_value), replace=True, p=(Fit) / (Fit.sum()))
        return idx

    def start(self, inputParam: HFSPGAInput) -> JSPGAResult:
        print('开始迭代计算' + ('最优' if inputParam.IsWorst is False else '最差') + '排产')
        J = {}
        J_num = 0
        M_num = 0
        for a in inputParam.ProcessingTime:
            J_num += 1
            J[J_num] = len(a)
            M_num = len(a[0])
        e = Encode(inputParam.ProcessingTime, self.Pop_size, J, J_num, M_num, inputParam.ProcessingGroup, inputParam.ProcessingWeight)
        OS_List=e.OS_List()
        Len_Chromo=e.Len_Chromo
        CHS1=e.Global_initial()
        CHS2 = e.Random_initial()
        CHS3 = e.Local_initial()
        C=np.vstack((CHS1,CHS2,CHS3))
        Optimal_fit=9999
        Optimal_CHS=0
        Best_fit=[]
        Worst_fit = []
        Avg_fit = []
        i = 0
        count = 0
        while True:
            i += 1
            Fit = self.fitness(C, J, inputParam, M_num, Len_Chromo)
            Best = C[Fit.index(min(Fit))]
            best_fitness = np.min(Fit)
            worst_fit = np.max(Fit) if inputParam.IsWorst is False else 1/np.max(Fit)
            avg_fit = np.average(Fit) if inputParam.IsWorst is False else np.average(np.reciprocal(Fit))
            print('第{0}轮迭代  best_fitness:{1} worst_fit:{2} avg_fit:{3}'.format(i, best_fitness, worst_fit, avg_fit))
            Worst_fit.append(worst_fit)
            Avg_fit.append(avg_fit)
            # d = Decode(J, Processing_time, M_num)
            # Optimal_CHS = C[Fit.index(max(Fit))]
            # Fit.append(d.Decode_1(Optimal_CHS, Len_Chromo))
            # d.Gantt(d.Machines)
            if best_fitness < Optimal_fit:
                count = 0
                Optimal_fit = best_fitness
                Optimal_CHS = Best.copy()
                Best_fit.append(Optimal_fit if inputParam.IsWorst is False else 1/Optimal_fit)
                print('best_fitness' if inputParam.IsWorst is False else 'worst_fitness', best_fitness if inputParam.IsWorst is False else  1 / best_fitness)
            else:
                Best_fit.append(Optimal_fit if inputParam.IsWorst is False else 1/Optimal_fit)
                count += 1
                if count > J_num or i > self.Max_Itertions:
                    break
            Select = self.Select(Fit)
            for j in range(len(C)):
                offspring = []
                if random.random()<self.P_c:
                    N_i = random.choice(np.arange(len(C)))
                    if random.random()<self.P_v:
                        Crossover=self.Crossover_Machine(C[j],C[N_i],Len_Chromo, J_num)
                        # print('Cov1----->>>>>',len(Crossover[0]),len(Crossover[1]))
                    else:
                        Crossover=self.Crossover_Operation(C[j],C[N_i],Len_Chromo,J_num, inputParam.ProcessingGroup)
                    Crossover = self.Crossover_Weight(Crossover[0], Crossover[1], Len_Chromo, J_num)
                    offspring.append(Crossover[0])
                    offspring.append(Crossover[1])
                    offspring.append(C[j])
                if random.random()<self.P_m:
                    if random.random()<self.P_w:
                        Mutation=self.Variation_Machine(C[j],inputParam.ProcessingTime,Len_Chromo,J, J_num)
                    else:
                        Mutation=self.Variation_Operation(C[j],Len_Chromo,J_num,J,inputParam,M_num)
                    Mutation = self.Variation_Weight(Mutation,Len_Chromo,J_num,J,inputParam, M_num)
                    offspring.append(Mutation)
                if len(offspring) > 0:
                    Fit = self.fitness(offspring, J, inputParam, M_num, Len_Chromo)
                    C[j] = offspring[Fit.index(min(Fit))]
        d = Decode(J, inputParam, M_num)
        if Optimal_CHS is int and Optimal_CHS == 0:
            raise Exception('无法完成排产')
        d.Decode_1(Optimal_CHS, Len_Chromo)
        return JSPGAResult(d, Best_fit, Worst_fit, Avg_fit, Optimal_CHS, Len_Chromo)

