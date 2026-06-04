$ErrorActionPreference = "Stop"

Write-Host "Fetching properties from Node A (t2.micro)..."
$nodeA = aws ec2 describe-instances --instance-ids i-004ede57a842280fe --region ap-south-1 | ConvertFrom-Json
$instance = $nodeA.Reservations[0].Instances[0]

$ami = $instance.ImageId
$subnet = $instance.SubnetId
$sg = $instance.SecurityGroups[0].GroupId
$iamProfile = $instance.IamInstanceProfile.Arn

Write-Host "Creating Node B (t3a.xlarge) The Cruncher..."

$runInstancesJson = aws ec2 run-instances `
    --image-id $ami `
    --instance-type t3a.xlarge `
    --subnet-id $subnet `
    --security-group-ids $sg `
    --iam-instance-profile Arn=$iamProfile `
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=project-intelligent-heavy-node}]" `
    --block-device-mappings "[{\`"DeviceName\`":\`"/dev/xvda\`",\`"Ebs\`":{\`"VolumeSize\`":16,\`"VolumeType\`":\`"gp3\`"}}]" `
    --region ap-south-1 | ConvertFrom-Json

$nodeBId = $runInstancesJson.Instances[0].InstanceId

Write-Host "Node B Created: $nodeBId"

Write-Host "Waiting 30 seconds for instance to initialize before stopping..."
Start-Sleep -Seconds 30

Write-Host "Stopping Node B immediately to prevent costs..."
aws ec2 stop-instances --instance-ids $nodeBId --region ap-south-1 | Out-Null

Write-Host "Creating CloudWatch Auto-Stop Fail-Safe Alarm..."

aws cloudwatch put-metric-alarm `
    --alarm-name "project-intelligent-heavy-node-idle-stop" `
    --alarm-description "Stops the t3a.xlarge instance if CPU is idle for 15 minutes as a cost fail-safe" `
    --namespace "AWS/EC2" `
    --metric-name "CPUUtilization" `
    --dimensions "Name=InstanceId,Value=$nodeBId" `
    --statistic "Average" `
    --period 300 `
    --evaluation-periods 3 `
    --threshold 2.0 `
    --comparison-operator "LessThanThreshold" `
    --alarm-actions "arn:aws:automate:ap-south-1:ec2:stop" `
    --region ap-south-1 | Out-Null

Write-Host "Done! Node B is provisioned, stopped, and protected."
Write-Host "NODE_B_ID=$nodeBId"
