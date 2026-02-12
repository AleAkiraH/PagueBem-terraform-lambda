FROM public.ecr.aws/lambda/python:3.11

# Install system dependencies for zbar and OpenCV
RUN dnf install -y \
    gcc \
    gcc-c++ \
    make \
    zbar \
    zbar-devel \
    libX11 \
    mesa-libGL \
    && dnf clean all

# Copy requirements and install Python packages
COPY requirements.txt ${LAMBDA_TASK_ROOT}/
RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt

# Copy application code
COPY . ${LAMBDA_TASK_ROOT}/

# Set the Lambda handler
CMD ["main.handler"]
