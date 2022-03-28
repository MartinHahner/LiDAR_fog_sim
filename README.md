Created by [Martin Hahner](https://sites.google.com/view/martinhahner/home) at the [Computer Vision Lab](https://vision.ee.ethz.ch/) of [ETH Zurich](https://ethz.ch/).

[![arXiv](https://img.shields.io/badge/arXiv-2108.05249-00ff00.svg)](https://arxiv.org/abs/2108.05249) [![PWC](https://img.shields.io/endpoint.svg?url=https://paperswithcode.com/badge/fog-simulation-on-real-lidar-point-clouds-for/3d-object-detection-on-stf)](https://paperswithcode.com/sota/3d-object-detection-on-stf?p=fog-simulation-on-real-lidar-point-clouds-for) ![visitors](https://visitor-badge.laobi.icu/badge?page_id=MartinHahner.LiDAR_fog_sim)


# [Fog Simulation on Real LiDAR Point Clouds <br> for 3D Object Detection in Adverse Weather](https://arxiv.org/abs/2108.05249)
*by [Martin Hahner](https://www.trace.ethz.ch/team/members/martin.html), [Christos Sakaridis](https://www.trace.ethz.ch/team/members/christos.html), [Dengxin Dai](https://www.trace.ethz.ch/team/members/dengxin.html), and [Luc van Gool](https://www.trace.ethz.ch/team/members/luc.html)*

Accepted at [ICCV 2021](http://iccv2021.thecvf.com). <br>
Please visit our [paper website](https://trace.ethz.ch/lidar_fog_sim) for more details.

![pointcloud_viewer](https://user-images.githubusercontent.com/14181188/115385936-0e033b00-a1d9-11eb-9d55-75969ae7ce47.gif)

## Overview

    .
    ├── file_lists                          # contains file lists for pointcloud_viewer.py
    │   └── ...
    ├── integral_lookup_tables              # contains lookup tables to speed up the fog simulation
    │   └── ... 
    ├── extract_fog.py                      # to extract real fog noise* from the SeeingThroughFog dataset
    ├── fog_simulation.py                   # to augment a clear weather pointcloud with artificial fog (used during training)
    ├── generate_integral_lookup_table.py   # to precompute the integral inside the fog equation
    ├── pointcloud_viewer.py                # to visualize entire point clouds of different datasets with the option to augment fog into their scenes
    ├── README.md
    └── theory.py                           # to visualize the theory behind a single LiDAR beam in foggy conditions


\* Contains returns not only from fog, but also from physical objects that are closeby.

**Datasets supported by `pointcloud_viewer.py`:**
- [H3D](https://usa.honda-ri.com/H3D)
- [A2D2](https://www.a2d2.audi/a2d2/en.html)
- [KITTI](http://www.cvlibs.net/datasets/kitti/eval_object.php?obj_benchmark=3d)
- [LyftL5](https://self-driving.lyft.com/level5/prediction/)
- [Pandaset](https://pandaset.org/)
- [nuScenes](https://www.nuscenes.org/nuscenes)
- [Argoverse](https://www.argoverse.org/data.html#tracking-link)
- [ApolloScape](http://apolloscape.auto/tracking.html)
- **[SeeingThroughFog](https://www.cs.princeton.edu/~fheide/AdverseWeatherFusion/)** &nbsp;:arrow_left: works best
- [WaymoOpenDataset](https://waymo.com/open/) (via [waymo_kitti_converter](https://github.com/caizhongang/waymo_kitti_converter))


## License

This software is made available for non-commercial use under a Creative Commons [License](LICENSE).<br>
A summary of the license can be found [here](https://creativecommons.org/licenses/by-nc/4.0/).


## Acknowledgments

This work is supported by [Toyota](https://www.toyota-europe.com/) via the [TRACE](https://www.trace.ethz.ch/) project.

Furthermore, we would like to thank the authors of [SeeingThroughFog](https://www.cs.princeton.edu/~fheide/AdverseWeatherFusion/) for their great work. <br>
In this repository, we use a [fork](https://github.com/MartinHahner/SeeingThroughFog) of [their original repository](https://github.com/princeton-computational-imaging/SeeingThroughFog) to visualize annotations and compare to their fog simulation. Their code is licensed via the [MIT License](https://github.com/princeton-computational-imaging/SeeingThroughFog/blob/master/LICENSE).

## Citation

If you find this work useful, please consider citing our paper.
```bibtex
@inproceedings{HahnerICCV21,
  author = {Hahner, Martin and Sakaridis, Christos and Dai, Dengxin and Van Gool, Luc},
  title = {{Fog Simulation on Real LiDAR Point Clouds for 3D Object Detection in Adverse Weather}},
  booktitle = {IEEE International Conference on Computer Vision (ICCV)},
  year = {2021},
}
```


## Getting Started

### Setup

1) Install [anaconda](https://docs.anaconda.com/anaconda/install/).

2) Create a new conda environment.

```bash
conda create --name foggy_lidar python=3.9 -y
```

3) Activate the newly created conda environment.

```bash
conda activate foggy_lidar
```

4) Install all necessary packages.

```bash
conda install matplotlib numpy opencv pandas plyfile pyopengl pyqt pyqtgraph quaternion scipy tqdm -c conda-forge -y
pip install pyquaternion
```

5) Clone this repository (including submodules).
```bash
git clone git@github.com:MartinHahner/LiDAR_fog_sim.git --recursive
cd LiDAR_fog_sim
```

### Usage

How to run the script that visualizes the theory behind a single LiDAR beam in foggy conditions:

```bash
python theory.py
```
![theory](https://user-images.githubusercontent.com/14181188/115370049-f9b74200-a1c8-11eb-88d0-474b8dd5daa3.gif)

How to run the script that visualizes entire point clouds of different datasets:

```bash
python pointcloud_viewer.py -d <path_to_where_you_store_your_datasets>
```

**Note:**

You may also have to adjust the relative paths in `pointcloud_viewer.py` (right at the beginning of the file) to be compatible with your datasets relative folder structure.

### Disclaimer

The code has been successfully tested on
- Ubuntu 18.04.5 LTS
- macOS Big Sur 11.2.1
- Debian GNU/Linux 9.13

using conda 4.9.2.


## Contributions
Please feel free to suggest improvements to this repository.<br> 
We are always open to merge usefull pull request.
