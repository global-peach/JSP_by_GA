import tornado.ioloop
import tornado.httpserver
import tornado.web
import json
import JSPGA

class MainHandler(tornado.web.RequestHandler):
    def post(self, *args, **kwargs):
        set_default_header(self)
        # json
        post_data = self.request.body.decode('utf-8')
        post_data = json.loads(post_data)
        print('开始迭代计算最优排产')
        g = JSPGA.GA()
        d = g.start(post_data.get('ProcessingTime'), post_data.get('ProcessingGroup'), post_data.get('MachineStartTime'), post_data.get('TimeEfficent'))[0]
        res = {}
        i = 0
        for Machine in d.Machines:
            mac = []
            Start_time=Machine.O_start
            End_time=Machine.O_end
            for i_1 in range(len(End_time)):
                mac.append({ "StartTime":int(Start_time[i_1]), "EndTime": int(End_time[i_1]), "Job": int(Machine.assigned_task[i_1][0] - 1)})
            res[str(i)]= mac
            i+=1
        self.write(res)
        print('完成')

def set_default_header(self):
    self.set_header('Access-Control-Allow-Origin', '*') 
    self.set_header('Access-Control-Allow-Headers', 'x-requested-with')
    self.set_header('Access-Control-Allow-Methods', 'POST, GET, PUT, DELETE') 



if __name__ == "__main__":
    application = tornado.web.Application([(r"/ga", MainHandler), ])
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(5241)
    print('监听端口:5241')
    tornado.ioloop.IOLoop.instance().start()