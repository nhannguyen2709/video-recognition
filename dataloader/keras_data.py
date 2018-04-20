import gc
import os
import numpy as np
import pickle
import random
from scipy import io

from cv2 import resize, imread
from sklearn.utils import shuffle
from keras.utils import Sequence, to_categorical


class UCF101(Sequence):
    def __init__(self, data_path, frame_counts_path, batch_size,
                 num_frames_sampled, num_classes, shuffle=True):
        self.data_path = data_path
        self.frame_counts = pickle.load(open(frame_counts_path, 'rb'))
        self.x, self.videos_dict = self.get_videos()
        self.y = self.labels_to_idxs()
        self.batch_size = batch_size
        self.num_frames_sampled = num_frames_sampled
        self.num_classes = num_classes
        self.shuffle = shuffle
        self.on_epoch_end()

    def on_epoch_end(self):
        if self.shuffle:
            self.x, self.y = shuffle(self.x, self.y)

    def labels_to_idxs(self):
        labels = sorted(set([video.split('_')[1] for video in self.x]))
        idxs = []
        for video in self.x:
            idxs.append(labels.index(video.split('_')[1]))
        return idxs

    def get_videos(self):
        video_clips = sorted(os.listdir(self.data_path))
        videos = sorted(set([clip[:-4] for clip in video_clips]))
        videos_dict = {}
        for video in videos:
            videos_dict[video] = {}
            videos_dict[video]['clips'] = [
                clip for clip in video_clips if clip.startswith(video)]
            videos_dict[video]['num_clips'] = len(videos_dict[video]['clips'])
        return videos, videos_dict

    def sample_clips(self, video):
        clips = np.array(self.videos_dict[video]['clips'])
        num_clips = self.videos_dict[video]['num_clips']
        sampled_clips_idx = sorted(np.random.choice(
            num_clips, size=4, replace=False))
        return clips[sampled_clips_idx]

    def sample_frames_snippet(self, clip_path, frame_count):
        frames = np.array([filename for filename in sorted(
            os.listdir(clip_path)) if filename.endswith('.jpg')])
        frames_snippet_idx = sorted(np.random.choice(
            frame_count, size=int(self.num_frames_sampled / 4), replace=False))
        return frames[frames_snippet_idx]

    def get_frame_count(self, sampled_clips):
        sampled_clip_frame_counts = [self.frame_counts[clip]
                                     for clip in sampled_clips]
        return sampled_clip_frame_counts

    def __len__(self):
        return int(np.ceil(len(self.x) / float(self.batch_size)))

    def __getitem__(self, idx):
        batch_x = self.x[idx * self.batch_size:(idx + 1) * self.batch_size]
        batch_y = self.y[idx * self.batch_size:(idx + 1) * self.batch_size]

        batch_video_frames = []
        for video in batch_x:
            sampled_clips = self.sample_clips(video)
            clip_paths = [os.path.join(self.data_path, clip)
                          for clip in sampled_clips]
            clip_frame_counts = self.get_frame_count(sampled_clips)
            clips_frames = [
                self.sample_frames_snippet(
                    clip_path, frame_count) for clip_path, frame_count in zip(
                    clip_paths, clip_frame_counts)]
            video_frames = []
            for clip_frames, clip_path in zip(clips_frames, clip_paths):
                video_frames.append([resize(imread(os.path.join(clip_path, frame)), (224, 224))
                                     for frame in clip_frames])
            video_frames = np.reshape(
                video_frames, (self.num_frames_sampled, 224, 224, 3))
            batch_video_frames.append(video_frames)
            del video_frames
            gc.collect()
        batch_video_frames = np.array(batch_video_frames)
        batch_video_frames = batch_video_frames / 255.

        return batch_video_frames, to_categorical(
            np.array(batch_y), num_classes=self.num_classes)


class PennAction(Sequence):
    def __init__(self, frames_path, labels_path, batch_size,
                 num_frames_sampled, num_classes, shuffle=True):
        self.frames_path = frames_path
        self.labels_path = labels_path
        self.get_videos_paths()
        self.extract_mat_file()
        print('Found {} videos belonging to {} classes'.format(len(self.x), len(self.labels)))
        self.batch_size = batch_size
        self.num_frames_sampled = num_frames_sampled
        self.num_classes = num_classes
        self.shuffle = shuffle
        self.on_epoch_end()

    def on_epoch_end(self):
        if self.shuffle:
            self.x, self.y, self.frame_counts = shuffle(
                self.x, self.y, self.frame_counts)

    def get_videos_paths(self):
        videos = sorted(os.listdir(self.frames_path))
        self.x = [os.path.join(self.frames_path, video)
                  for video in videos]

    def extract_mat_file(self):
        list_mat_files = sorted(os.listdir(self.labels_path))
        y = np.empty(len(list_mat_files), dtype=object)
        frame_counts = np.empty(len(list_mat_files), dtype=int)
        for i, mat_file in enumerate(list_mat_files):
            mat = io.loadmat(os.path.join(self.labels_path, mat_file))
            frame_counts[i] = mat['nframes'][0][0]
            y[i] = mat['action'][0]
            
        self.frame_counts = frame_counts
        self.labels = sorted(set(y))
        self.y = np.vectorize(lambda x: self.labels.index(x))(
            y)  # convert label into class

    def sample_frames(self, video_path, frame_count):
        all_frames = np.array([filename for filename in sorted(
            os.listdir(video_path)) if filename.endswith('.jpg')])
        sampled_frames_idx = sorted(np.random.choice(
            frame_count, size=int(self.num_frames_sampled), replace=False))
        return sampled_frames_idx, all_frames[sampled_frames_idx]
    
    def __len__(self):
        return int(np.ceil(len(self.x) / float(self.batch_size)))

    def __getitem__(self, idx):
        batch_x = self.x[idx * self.batch_size:(idx + 1) * self.batch_size]
        batch_y = self.y[idx * self.batch_size:(idx + 1) * self.batch_size]
        
        batch_mat_files = [video_path.replace('frames/', 'labels/') for video_path in batch_x]
        batch_frame_counts = self.frame_counts[idx * \
            self.batch_size:(idx + 1) * self.batch_size]
        batch_video_frames = np.zeros(
            (self.batch_size, self.num_frames_sampled, 224, 224, 3))
        batch_video_poses = np.zeros(
            (self.batch_size, self.num_frames_sampled, 26))

        for i, video_path in enumerate(batch_x):
            sampled_frames_idx, sampled_frames = self.sample_frames(
                video_path, batch_frame_counts[i])
            # extract video frames
            batch_video_frames[i] = [
                resize(
                    imread(
                        os.path.join(
                            video_path,
                            frame)),
                    (224,
                     224)) for frame in sampled_frames]
            # extract poses from sampled frames
            first_frame = imread(os.path.join(video_path, sampled_frames[0]))
            x_max, y_max = first_frame.shape[:2]
            mat = io.loadmat(batch_mat_files[i])
            # normalize poses coordinates
            poses_x, poses_y = mat['x'] / x_max, mat['y'] / y_max
            poses_x_y = np.hstack([poses_x, poses_y])
            poses_x_y = poses_x_y[sampled_frames_idx]
            batch_video_poses[i] = poses_x_y

        batch_video_frames = batch_video_frames / 255.

        return [batch_video_frames, batch_video_poses], to_categorical(
            np.array(batch_y), num_classes=self.num_classes)


if __name__=='__main__':
    penn_action = PennAction(frames_path='data/Penn_Action/frames', 
                             labels_path='data/Penn_Action/labels',
                             batch_size=8, num_frames_sampled=16, num_classes=15,
                             shuffle=False)

    x, y = penn_action.__getitem__(0)
    print(x[0].shape, x[1].shape)
    