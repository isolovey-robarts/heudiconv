Bootstrap: docker
From: ubuntu:xenial

#note: install_afni_fsl_sudo.sh solves error message when run itksnap: LibGlu.so.1

#run freesurfer's freeview 
# if libQtOpenGL.so.4, run sudo apt-get libqt4-dev
# if missing:  libjpeg.so.62, run apt-get install libjpeg62

#create image
#rm ~/neuroglia/neuroglia.img && singularity create  --size 20000 ~/neuroglia/neuroglia.img && sudo singularity bootstrap ~/neuroglia/neuroglia.img Singularity

#########
%setup
#########
cp ./install_scripts/*.sh $SINGULARITY_ROOTFS

#########
%post
#########

export DEBIAN_FRONTEND=noninteractive
bash 00.install_basics_sudo.sh
bash 03.install_anaconda2_nipype_dcmstack_by_binary.sh /opt
bash 23.install_heudiconv_by_source.sh /opt



#remove all install scripts
rm *.sh


#########
%environment


#anaconda2
export PATH=/opt/anaconda2/bin/:$PATH


#heudiconv
export PYTHONPATH=/opt/heudiconv:$PYTHONPATH

