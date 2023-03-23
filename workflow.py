from modelarts import workflow as wf
from modelarts.session import Session
import argparse


def train_options():
    parser = argparse.ArgumentParser()
    parser.add_argument("--access_key", help='ak')
    parser.add_argument("--secret_key", help='sk')
    parser.add_argument("--project_id", help='project id', )
    parser.add_argument("--obs_bucket_name", help='obs bucket name')
    parser.add_argument("--project_name", help='project name')
    args = parser.parse_args()
    return args


opt = train_options()

# 通过用户传入的ak和sk创建该用户的session，用于云服务的鉴权
session = Session(access_key=opt.access_key, secret_key=opt.secret_key, project_id=opt.project_id,
                  region_name="cn-north-4")

# 统一输出目录配置
output_storage = wf.data.Storage(name="output_storage", description="统一输出目录配置", with_execution_id=True,
                                 default='/cnnorth4/workflow_cicd/')
# 数据集路径
data_path = wf.data.OBSPath(obs_path="/{}/{}/data/".format(opt.obs_bucket_name, opt.project_name))
# 训练输出路径
train_output = output_storage.join("/train_output", create_dir=True)
# metrics文件路径
metric_file = output_storage.join("/train_output/metrics.json")

# 训练节点定义
job_step = wf.steps.JobStep(
    name="training",
    title="模型训练",
    algorithm=wf.BaseAlgorithm(
        code_dir="obs://{}/{}/".format(opt.obs_bucket_name, opt.project_name),
        command='python ${{MA_JOB_DIR}}/{}/training.py'.format(opt.project_name),
        engine=wf.steps.JobEngine(image_url="hwstaff_maexp/torch1.8-dxh:v001"),
    ),
    inputs=[wf.steps.JobInput(name="data_url",
                              data=wf.data.OBSPlaceholder(name="dataset_input", object_type="directory",
                                                          default=data_path))],
    outputs=[wf.steps.JobOutput(name="train_url", obs_config=wf.data.OBSOutputConfig(obs_path=train_output)),
             wf.steps.JobOutput(
                 name="metrics",
                 metrics_config=wf.data.MetricsConfig(metric_files=metric_file, realtime_visualization=True)
             )],
    spec=wf.steps.JobSpec(
        resource=wf.steps.JobResource(
            flavor_id=wf.Placeholder(name="training_flavor",
                                     placeholder_type=wf.PlaceholderType.STR,
                                     default="modelarts.vm.cpu.8u",
                                     description="训练资源规格")
        )
    )
)

# 模型注册节点
model_registration = wf.steps.ModelStep(
    name="model_registration",
    title="模型注册",
    inputs=[wf.steps.ModelInput(name="model_file", data=job_step.outputs["train_url"].as_input())],
    outputs=wf.steps.ModelOutput(name='model_output',
                                 model_config=wf.steps.ModelConfig(model_name="mnist_test", model_type="PyTorch")),
    depend_steps=[job_step]
)

# workflow定义
workflow = wf.Workflow(name="demo_ct_workflow",
                       desc="This is a demo workflow for continuous training",
                       steps=[job_step, model_registration],
                       session=session,
                       storages=[output_storage]
                       )
# workflow发布到console并运行
workflow.release_and_run()
