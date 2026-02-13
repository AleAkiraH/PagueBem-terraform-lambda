FROM public.ecr.aws/lambda/python:3.11

# Install system dependencies for OpenCV and building zbar from source
RUN yum install -y \
    gcc \
    gcc-c++ \
    make \
    autoconf \
    automake \
    libtool \
    pkgconfig \
    gettext-devel \
    libX11 \
    mesa-libGL \
    && yum clean all

# Build and install zbar from source (not available in Amazon Linux 2 repos)
RUN cd /tmp \
    && curl -L -o zbar-0.23.93.tar.gz https://github.com/mchehab/zbar/archive/refs/tags/0.23.93.tar.gz \
    && tar xzf zbar-0.23.93.tar.gz \
    && cd zbar-0.23.93 \
    && autoreconf -vfi \
    && ./configure --prefix=/usr --without-gtk --without-qt --without-python --without-java --disable-video --without-imagemagick --without-xv --without-xshm --without-dbus --without-graphicsmagick \
    && make -j$(nproc) \
    && make install \
    && echo "/usr/lib" > /etc/ld.so.conf.d/zbar.conf \
    && /sbin/ldconfig \
    && cd / \
    && rm -rf /tmp/zbar-*

# Copy requirements and install Python packages
COPY requirements.txt ${LAMBDA_TASK_ROOT}/
RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt

# Copy application code
COPY . ${LAMBDA_TASK_ROOT}/

# Set the Lambda handler
CMD ["main.handler"]
