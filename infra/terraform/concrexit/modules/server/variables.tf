variable "tags" {
  description = "AWS tags for resources"
  type        = map(string)
}

variable "stage" {
  description = "Deployment stage for resource names"
  type        = string
}

variable "customer" {
  description = "Customer prefix for resource names"
  type        = string
}

variable "aws_interface_id" {
  description = "ID of the AWS network interface to attach to the EC2 instance"
  type        = string
}

variable "ssh_public_key" {
  description = "SSH public key to use to SSH into the EC2 instance"
  type        = string
}

variable "ec2_instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3a.small"
}

variable "ec2_ami" {
  description = "EC2 AMI"
  type        = string
  default     = "ami-089f338f3a2e69431" # Debian 11 (amd64, eu-west-1)
}
