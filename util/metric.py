import json
import os
import time


def get_timestamp():
    return int(round(time.time()*1000))


class Metric(object):

    def __init__(self, key, title=''):
        self.key = key
        if title:
            self.title = title
        else:
            self.title = key

    def to_json(self):
        result = {
            "key": self.key,
            "title": self.title,
        }
        return result


class ListMetric(Metric):

    def __init__(self, key, title=''):
        super().__init__(key, title)
        self.type = "line chart"
        self.steps = []
        self.timestamps = []
        self.values = []

    def to_json(self):
        result = super().to_json()
        result["type"] = self.type
        result["data"] = {
            "x_axis": [
                {
                    "title": "step",
                    "value": self.steps,
                },
                {
                    "title": "timestamp",
                    "value": self.timestamps
                }
            ],
            "y_axis": [
                {
                    "title": "value",
                    "value": self.values
                }
            ]
        }

        return result

    def add_value(self, value, step=0):
        self.steps.append(step)
        self.timestamps.append(get_timestamp())
        self.values.append(value)


class MetricLogger(object):

    def __init__(self, output_url, file_name):
        self.output_url = output_url
        self.file_name = file_name
        self.metrics = {}

    def output_metrics(self):
        output = []
        for value in self.metrics.values():
            output.append(value.to_json())
        local_metrics_path = os.path.join(self.output_url, self.file_name)
        with open(local_metrics_path, 'w') as f:
            json.dump(output, f, indent=4, separators=(',', ':'))

    def log_metric(self, key, value, title=None, step=0):
        if key in self.metrics.keys():
            metric = self.metrics[key]
            metric.add_value(value, step)
            self.metrics[key] = metric
        else:
            metric = ListMetric(key, title)
            metric.add_value(value, step)
            self.metrics[key] = metric

        self.output_metrics()
