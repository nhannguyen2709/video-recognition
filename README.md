# Video recognition
This repository aims to replicate the main results from several papers in the field of action recognition on videos as well as try out new architectures using Keras, Numpy and OpenCV. All models can be found in the `keras_models.py` file.
## Reference papers
> 
**Two-Stream Convolutional Networks for Action Recognition in Videos**,
Karen Simonyan, Andrew Zisserman,
*NIPS 2014*.
[[Arxiv Preprint](https://arxiv.org/pdf/1406.2199.pdf)]
> 
**Long-term Recurrent Convolutional Networks for Visual Recognition and Description**,
Jeff Donahue, Lisa Anne Hendricks, Marcus Rohrbach, Subhashini Venugopalan, Sergio Guadarrama, Kate Saenko, Trevor Darrell,
*CVPR 2015*.
[[Arxiv Preprint](https://arxiv.org/pdf/1411.4389.pdf)]
> 
**Temporal Segment Networks: Towards Good Practices for Deep Action Recognition**,
Limin Wang, Yuanjun Xiong, Zhe Wang, Yu Qiao, Dahua Lin, Xiaoou Tang, Luc Van Gool,
*ECCV 2016*.
[[Arxiv Preprint](https://arxiv.org/pdf/1705.02953.pdf)]
> 
**Two-Stream RNN/CNN for Action Recognition in 3D Videos**,
Rui Zhao, Haider Ali, Patrick van der Smagt,
*2017 IEEE/RSJ International Conference on Intelligent Robots and Systems (IROS)*.
[[Arxiv Preprint](https://arxiv.org/pdf/1703.09783.pdf)]
> 
**VideoLSTM Convolves, Attends and Flows for Action Recognition**,
Zhenyang Li, Efstratios Gavves, Mihir Jain, Cees G. M. Snoek,
*Computer Vision and Image Understanding 2018*.
[[Arxiv Preprint](https://arxiv.org/pdf/1607.01794.pdf)]

## 1. Data
  ### 1.1 UCF101 Dataset 
  Download the preprocessed data directly from [feichtenhofer/twostreamfusion](https://github.com/feichtenhofer/twostreamfusion)
  * RGB images
  ```
  wget http://ftp.tugraz.at/pub/feichtenhofer/tsfusion/data/ucf101_jpegs_256.zip.001
  wget http://ftp.tugraz.at/pub/feichtenhofer/tsfusion/data/ucf101_jpegs_256.zip.002
  wget http://ftp.tugraz.at/pub/feichtenhofer/tsfusion/data/ucf101_jpegs_256.zip.003
  
  cat ucf101_jpegs_256.zip* > ucf101_jpegs_256.zip
  unzip ucf101_jpegs_256.zip
  ```
  * Optical Flow
  ```
  wget http://ftp.tugraz.at/pub/feichtenhofer/tsfusion/data/ucf101_tvl1_flow.zip.001
  wget http://ftp.tugraz.at/pub/feichtenhofer/tsfusion/data/ucf101_tvl1_flow.zip.002
  wget http://ftp.tugraz.at/pub/feichtenhofer/tsfusion/data/ucf101_tvl1_flow.zip.003
  
  cat ucf101_tvl1_flow.zip* > ucf101_tvl1_flow.zip
  unzip ucf101_tvl1_flow.zip
  ```
  ### 1.2 PennAction Dataset
  Available for download via the following link: https://upenn.box.com/PennAction
  ### 1.3 MyVideos Dataset
  Consists of 80 own recorded videos on 5 different actions (PickUpObject, TakeOffShoes, TakeOffClothes, Stealing and NotStealing). RGB   frames and human poses from each video in this dataset were extracted using `OpenCV` and [CMU's OpenPose](https://github.com/CMU-Perceptual-Computing-Lab/openpose) libraries.

## 2. Training
  ### 2.1 Temporal Segment Networks (TSN)
  The original paper used the BN-InceptionV3 pre-trained on ImageNet as the base conv. network. I used the [pre-trained Xception network provided in Keras](https://github.com/keras-team/keras/blob/master/keras/applications/xception.py) as my base model. Training strategies and implementation details of the original paper such as partial batch-normalization with dropout, using SGD optimizer, learning rate schedules were followed closely. Training data augmentation and ImageNet-style test-time augmentation will be added soon.
  ### 2.2 Two-stream RNN-CNN / VideoLSTM
  I made a tweak to combine the architectures from these two papers. To process RGB frames, I used a time-distributed, pre-trained VGG19 with a global max pooling layer after the last convolutional layer. The video representation learned by the VGG19 will be then fed into a 2 layer GRU network. The 2D human poses obtained in every sampled frame will be fed into a 3 layer GRU network. I fuse the frames stream and poses stream predictions by averaging their softmax outputs.
  
 ## 3. Results
  ### UCF101

| Accuracy (%)                      | RGB   | Flow  | RGB+Flow |
|-----------------------------------|-------|-------|----------|
| Xception (avg consensus, no TTA)  | 84.51 |       |          |
| Xception (attention, no TTA)      | 83.64 |       |          |
| Xception (max consensus, no TTA)  | 82.95 |       |          |

  ### Penn Action
| Accuracy (%)                      | RGB+Poses|
|-----------------------------------|----------|
| Two-stream VGG19-GRU              | 93.52    |

## 4. Run on your device
* Training:
>
On a single GTX 1070Ti, training the TSN's spatial stream on UCF101 data took approximately 7.5 hours; training the two-stream VGG19-GRU on Penn Action data took approximately 3 hours.
```
python3 train_tsn_spatial_stream.py
python3 train_tsn_motion_stream.py
python3 train_on_my_videos.py
python3 train_on_penn_action_dataset.py
```
* Testing:
>
Only on Penn Action dataset
```
python3 predict.py
```

## 5. TODO
`TODO Train the motion stream of the Temporal Segment Networks`
>
`TODO Add data augmentation when training networks`
>
`TODO Apply test-time augmentation to improve models' performance`
