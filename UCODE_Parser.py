input_file="""
BEGIN Options Keywords
  Verbose = {verbose}
END Options

BEGIN UCODE_Control_Data Keywords
  ModelName = {modelname}
  ModelLengthUnits = m
  ModelTimeUnits = day
  sensitivities=yes
  optimize=no
  StartSens=css
  IntermedSens=css
  FinalSens=css
END UCODE_Control_Data

BEGIN PARALLEL_CONTROL 
 OPERATINGSYSTEM=Linux 
 Parallel=yes 
 Wait=.001 
 VerboseRunner=3 
 AutoStopRunners=yes 
END PARALLEL_CONTROL

BEGIN Model_Command_Lines Keywords
  Command = {command}
  CommandID=ForwardModel
END Model_Command_Lines

BEGIN PARAMETER_GROUPS KEYWORDS
    groupname=Default adjustable=yes tolpar=0.005
END PARAMETER_GROUPS

BEGIN PARAMETER_DATA FILES
  {params}
END PARAMETER_DATA

BEGIN Observation_Groups Table
  NROW=2 NCOL=3 COLUMNLABELS
  GroupName PlotSymbol UseFlag
  Modelhead 1 yes
  Modelflows 2 yes
END Observation_Groups

BEGIN OBSERVATION_DATA FILES
  {observations_heads}
  {observations_flows}
END OBSERVATION_DATA

BEGIN MODEL_INPUT_FILES KEYWORDS
  modinfile={modinfile}
  templateFile={in_template}
END MODEL_INPUT_FILES

BEGIN MODEL_OUTPUT_FILES TABLE
 nrow=2 ncol=3 columnlabels
 modoutfile instructionfile category
 {modoutfile_heads} {instructionsfile_heads} obs
 {modoutfile_flows} {instructionsfile_flows} obs
END MODEL_OUTPUT_FILES

"""

#number of rows
# K, SS, Rcharge
# @ParName .......@, @P..
input_template="""jtf @
{}
"""

# NumofObs
# [ObsName...]
output_template="""jif @
StandardFile 0 1 {}
{}
"""

observations="""
BEGIN OBSERVATION_DATA TABLE
  NROW={} NCOL=4 COLUMNLABELS GroupName={}
  ObsName ObsValue Statistic Statflag
  {}
END OBSERVATION_DATA
"""

parameters="""
BEGIN PARAMETER_DATA TABLE
  NROW={} NCOL=7 COLUMNLABELS GroupName=Default
  ParamName StartValue LowerValue UpperValue PERTURBAMT TRANSFORM MAXCHANGE 
  {}
END PARAMETER_DATA
"""

import pandas as pd


class UCODEParser(object):
    """docstring for UCODEParser."""
    def __init__(self, arg=None):
        super(UCODEParser, self).__init__()
        self.arg = arg

    params = {
    #StartValue LowerValue UpperValue PERTURBAMT TRANSFORM MAXCHANGE
    #e.g.    "K": [1,0.001,10,0.01,"yes",2.0]
    }

    options = {
        "verbose": '5',
        "modelname": 'A model name',
        "command": './abinary',
        "params": 'par',
        "observations_heads": 'heads',
        "observations_flows": 'flows',
        "modinfile": 'input.csv',
        "in_template": 'in.jtf',
        "modoutfile_heads": 'output.csv',
        "modoutfile_flows": 'delta.csv',
        "instructionsfile_heads": 'out.jif',
        "instructionsfile_flows": 'flows.jif'
    }

    def read_observations(self, only_ids=False):
        #read in observations ID,Val
        df_heads = pd.read_csv('obs.csv', sep=',')
        df_flows = pd.read_csv('flows_ob.csv', sep=',')
        groups = ['Modelhead','Modelflows']
        df_heads['Stat'] = 0.3
        df_heads['Flag'] = 'CV'
        df_flows['Stat'] = 0.1
        df_flows['Flag'] = 'CV'
        df_heads['ID'].astype(str)
        df_flows['ID'].astype(str)
        df_heads['ID'] = df_heads.apply(lambda row: 'obs{}'.format(row['ID']), axis=1)
        df_flows['ID'] = df_flows.apply(lambda row: 'obsF{}'.format(row['ID']), axis=1)
        if only_ids:
            #df_f['ID'] = df_f.apply(lambda row: '!{}!'.format(row['ID']), axis=1)
            #df_m['ID'] = df_m.apply(lambda row: '!{}!'.format(row['ID']), axis=1)
            df = df_heads['ID']
            s_heads =  str(df.to_csv(index=False,header=False,sep=' '))
            df = df_flows['ID']
            s_flows =  str(df.to_csv(index=False,header=False,sep=' '))
            return len(df_heads.index), len(df_flows.index), s_heads , s_flows
        else:
            df_heads = df_heads[['ID', 'Head', 'Stat', 'Flag']]
            df_flows = df_flows[['ID', 'Flow', 'Stat', 'Flag']]
        valsHeads = str(df_heads.to_csv(index=False, header=False, sep=' '))
        valsFlows = str(df_flows.to_csv(index=False, header=False, sep=' '))
        return len(df_heads.index), len(df_flows.index), valsHeads, valsFlows, groups

    def parse_output_template(self):
        rows1,rows2,data1,data2 = self.read_observations(True)
        return output_template.format(rows1, data1), output_template.format(rows2, data2)

    def parse_input_template(self):
        #rows = len(self.params)
        data = 'name,val\n'
        for key,value in self.params.items():
            data += str(key) + ','+'@{}                     @'.format(key) + '\n'
        return input_template.format(data)

    def parse_observations(self):
        rows_f,rows_m,data_f,data_m,gr = self.read_observations()
        obs_f = observations.format(rows_f,gr[0], data_f)
        obs_m = observations.format(rows_m,gr[1], data_m)
        return obs_f, obs_m

    def parse_parameters(self):
        rows = len(self.params)
        #ParamName StartValue LowerValue UpperValue PERTURBAMT TRANSFORM MAXCHANGE
        data = ''
        for key, value in self.params.items():
            data += key + " " + str(value[0]) + " " + str(value[1]) + " " + str(value[2]) + " " + str(value[3]) + " " + str(value[4]+ " " + str(value[5])) + '\n'
        par_def = parameters.format(rows,data)
        return par_def

    #write current state to file
    @staticmethod
    def write_to_file(filename, string):
        with open(filename, "w") as text_file:
            print(string.rstrip(), file=text_file)

    def write_config(self, filename):
        self.write_to_file(filename, input_file.format(** self.options))

    def write_observations(self):
        obs_heads,obs_flows = self.parse_observations()
        self.write_to_file(self.options['observations_heads'],obs_heads)
        self.write_to_file(self.options['observations_flows'],obs_flows)

    def write_parameters(self):
        self.write_to_file(self.options['params'],self.parse_parameters())

    def write_templates(self):
        self.write_to_file(self.options['in_template'],self.parse_input_template())
        t1,t2 = self.parse_output_template()
        self.write_to_file(self.options['instructionsfile_heads'], t1)
        self.write_to_file(self.options['instructionsfile_flows'], t2)

    def write(self,filename):
        self.write_config(filename)
        self.write_observations()
        self.write_parameters()
        self.write_templates()
