import math


class ObjDimensions():
    def __init__(self,x = 0.0, y= 0.0, z = 0.0):
        self.x = x
        self.y = y
        self.z = z  

    @classmethod
    def create_from_list(cls, my_list):
        # float() strips the "NumPy-ness" off the number and makes it native
        return cls(
            float(my_list[0]), 
            float(my_list[1]), 
            float(my_list[2])
        )

    def update_from_list(self, list):
        
        
        self.x= float(list[0]) 
        self.y= float(list[1]) 
        self.z= float(list[2])
            

class ObjPosition(ObjDimensions):
    pass
   


def metric_to_imp_array(self,metric_array=list,x = None, y = None, z = None):
    imp_array = []

    for met in metric_array:
        imp = met/25.4
        imp_array.append(imp)

    return imp_array


def imp_to_metric_array(self,imp_array = list):
    metric_array = []

    for imp in imp_array:
        metric = imp*25.4
        metric_array.append(metric)

    return metric_array

def metric_to_imp(metric):
    return metric/25.4

def imp_to_metric(imp):
        return imp*25.4
    