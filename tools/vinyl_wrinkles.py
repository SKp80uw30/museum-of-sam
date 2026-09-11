"""Tileable irregular gathered-vinyl normal map, returned in linear RGB."""
import numpy as np
import math

def wrinkle_normal(size=1024):
 v,u=np.mgrid[0:size,0:size].astype(np.float32)/size
 rng=np.random.default_rng(48271)
 x=u+.032*np.sin(v*math.tau*3)+.012*np.sin((u*4+v*2)*math.tau)
 y=v+.027*np.sin(u*math.tau*2)+.014*np.sin((v*5-u*3)*math.tau)
 height=np.zeros_like(u)
 for i in range(36):
  kx=int(rng.integers(8,65));ky=int(rng.integers(-12,13));phase=rng.uniform(0,math.tau)
  height+=rng.uniform(.000045,.00013)*np.sin(math.tau*(kx*x+ky*y)+phase)
 # Crumpling at several scales prevents straight repeating corrugation.
 for i in range(12):
  kx=int(rng.integers(-9,10));ky=int(rng.integers(5,25));phase=rng.uniform(0,math.tau)
  height+=rng.uniform(.00008,.00022)*np.sin(math.tau*(kx*x+ky*y)+phase)
 gy,gx=np.gradient(height,1/size)
 normal=np.stack([-gx,-gy,np.ones_like(gx)],-1)
 normal/=np.linalg.norm(normal,axis=-1,keepdims=True)
 return normal*.5+.5
