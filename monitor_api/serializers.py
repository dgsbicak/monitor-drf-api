from rest_framework import serializers
from django.contrib.auth.models import User

from .models import Machine, MachineInfo


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username"]


class MachineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Machine
        fields = ["created", "machinename", "machineid", 
            "hasgpu", "machinetype"]

class MachineInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = MachineInfo
        fields = ["machine","created","cpuutil","cpumem","gpuutil","gpumem","diskspaceleft",
            "disk_r","disk_w","network_r","network_t","internet_access","running",
        ]