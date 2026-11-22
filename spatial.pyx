# cython: language_level=3, boundscheck=False, wraparound=False, initializedcheck=False, cdivision=True
"""Hot ray queries for a bilinear terrain and a grid of polygon prisms."""
from libc.math cimport sqrt, ceil, floor, INFINITY, isnan
from cython cimport final

cdef inline int bound(int x, int limit) noexcept:
    return 0 if x < 0 else (limit-1 if x >= limit else x)

@final
cdef class Geometry:
    cdef int nx, ny, gnx, gny, tbnx
    cdef double ox,oy,step,gx,gy,maxz
    cdef float[:] h, bounds
    cdef int[:] eoff, eids, poff,pids, holes,starts
    cdef double[:] edges, prism, verts

    def __init__(self, w, h, bounds, eoff,eids,poff,pids,holes,starts,edges,prism,verts):
        self.nx,self.ny,self.ox,self.oy,self.step = w.NX,w.NY,w.TMinX,w.TMinY,w.TStep
        self.gnx,self.gny,self.gx,self.gy,self.maxz=w.gnx,w.gny,w.gx,w.gy,w.TerrainMax
        self.tbnx=(self.nx+15)//16
        self.h,self.bounds,self.eoff,self.eids,self.poff,self.pids=h,bounds,eoff,eids,poff,pids
        self.holes,self.starts,self.edges,self.prism,self.verts=holes,starts,edges,prism,verts

    cdef inline double sample(self,double x,double y) noexcept:
        cdef double fx=(x-self.ox)/self.step, fy=(y-self.oy)/self.step
        fx=min(max(fx,0.),self.nx-1.)
        fy=min(max(fy,0.),self.ny-1.)
        cdef int i=min(<int>fx,self.nx-2), j=min(<int>fy,self.ny-2), k=j*self.nx+i
        fx-=i
        fy-=j
        return (self.h[k]*(1-fx)+self.h[k+1]*fx)*(1-fy)+(self.h[k+self.nx]*(1-fx)+self.h[k+self.nx+1]*fx)*fy

    cpdef double TerrainZ(self,double x,double y):
        return self.sample(x,y)

    cdef inline int cell(self,double x,double y) noexcept:
        return bound(<int>((y-self.gy)/8.),self.gny)*self.gnx+bound(<int>((x-self.gx)/8.),self.gnx)

    cdef inline bint inside(self,int p,double x,double y) noexcept:
        cdef int r,idx,prior,start,end,base=p*6
        cdef bint hit
        cdef double yi,yj,xi,xj
        if x<self.prism[base+2] or y<self.prism[base+3] or x>self.prism[base+4] or y>self.prism[base+5]:return False
        for r in range(self.holes[p],self.holes[p+1]):
            start=self.starts[r];end=self.starts[r+1];prior=end-2;hit=False
            for idx in range(start,end,2):
                yi=self.verts[idx+1];yj=self.verts[prior+1]
                if (yi>y)!=(yj>y):
                    xi=self.verts[idx];xj=self.verts[prior]
                    if x<(xj-xi)*(y-yi)/(yj-yi)+xi:hit=not hit
                prior=idx
            if r==self.holes[p]:
                if not hit:return False
            elif hit:return False
        return True

    cpdef tuple Floor(self,double x,double y,double z):
        cdef double h=self.sample(x,y),top
        cdef int c=self.cell(x,y),on=-1,p,i
        for i in range(self.poff[c],self.poff[c+1]):
            p=self.pids[i];top=self.prism[p*6+1]
            if h<top<=z and self.inside(p,x,y):h=top;on=p
        return h,on

    cdef inline double block(self,double x,double y) noexcept:
        cdef int i=bound(<int>((x-self.ox)/self.step),self.nx), j=bound(<int>((y-self.oy)/self.step),self.ny)
        return self.bounds[(j//16)*self.tbnx + i//16]

    cdef double terrain(self,double ox,double oy,double oz,double dx,double dy,double dz,double limit) noexcept:
        if oz>self.maxz and oz+dz*limit>self.maxz:return limit
        cdef double t=0,prev=0,ph=oz-self.sample(ox,oy),x0,y0,z0,x1,y1,z1,m0,m1,s,h,lo,hi,mid
        cdef int i
        if ph<0:return 0
        while t<limit:
            if t+8<limit:
                x0=ox+dx*t;y0=oy+dy*t;z0=oz+dz*t
                x1=x0+dx*8;y1=y0+dy*8;z1=z0+dz*8
                m0=self.block(x0,y0);m1=self.block(x1,y1)
                if min(z0,z1)>m0+.3 and min(z0,z1)>m1+.3:
                    t+=8;prev=t;ph=z1-m1
                    continue
            t=min(limit,t+max(1.,min(12.,ph*.5)))
            h=oz+dz*t-self.sample(ox+dx*t,oy+dy*t)
            if h<0:
                lo=prev;hi=t
                for i in range(12):
                    mid=(lo+hi)*.5
                    if oz+dz*mid-self.sample(ox+dx*mid,oy+dy*mid)<0:hi=mid
                    else:lo=mid
                return lo
            prev=t;ph=h
        return limit

    cdef double cast(self,double ox,double oy,double oz,double dx,double dy,double dz,double limit) noexcept:
        if isnan(ox) or isnan(oy) or isnan(oz) or isnan(dx) or isnan(dy) or isnan(dz):return limit
        if isnan(limit) or limit<=0:return 0
        cdef double best=limit,tx=INFINITY,ty=INFINITY,dtx=INFINITY,dty=INFINITY,enter=0,exit
        cdef int i=<int>floor((ox-self.gx)/8.),j=<int>floor((oy-self.gy)/8.),si=0,sj=0
        cdef int e,k,p,c,guard
        cdef double ex,ey,den,ax,ay,t,s,z,plane
        if i>=0 and j>=0 and i<self.gnx and j<self.gny:
            if dx>1e-12:si=1;tx=(self.gx+(i+1)*8.-ox)/dx;dtx=8./dx
            elif dx<-1e-12:si=-1;tx=(self.gx+i*8.-ox)/dx;dtx=-8./dx
            if dy>1e-12:sj=1;ty=(self.gy+(j+1)*8.-oy)/dy;dty=8./dy
            elif dy<-1e-12:sj=-1;ty=(self.gy+j*8.-oy)/dy;dty=-8./dy
            for guard in range(2*(self.gnx+self.gny)+8):
                c=j*self.gnx+i;exit=min(tx,ty)
                for k in range(self.eoff[c],self.eoff[c+1]):
                    e=self.eids[k]*6;ex=self.edges[e+2]-self.edges[e];ey=self.edges[e+3]-self.edges[e+1]
                    den=dx*ey-dy*ex
                    if -1e-12<den<1e-12:continue
                    ax=self.edges[e]-ox;ay=self.edges[e+1]-oy;t=(ax*ey-ay*ex)/den
                    if t<=1e-9 or t>=best:continue
                    s=(ax*dy-ay*dx)/den
                    if s<0 or s>1:continue
                    z=oz+t*dz
                    if self.edges[e+4]<=z<=self.edges[e+5]:best=t
                if dz<-1e-9 or dz>1e-9:
                    for k in range(self.poff[c],self.poff[c+1]):
                        p=self.pids[k]
                        if dz<0:
                            plane=self.prism[p*6+1]
                            if oz<plane:continue
                        else:
                            plane=self.prism[p*6]
                            if oz>plane:continue
                        t=(plane-oz)/dz
                        if t<enter-1e-6 or t>exit+1e-6 or t>=best or t<0:continue
                        if self.inside(p,ox+t*dx,oy+t*dy):best=t
                if exit>=best:break
                enter=exit
                if tx<ty:i+=si;tx+=dtx
                else:j+=sj;ty+=dty
                if i<0 or j<0 or i>=self.gnx or j>=self.gny:break
        return self.terrain(ox,oy,oz,dx,dy,dz,best)

    cpdef double Raycast(self,double ox,double oy,double oz,double dx,double dy,double dz,double distance):
        return self.cast(ox,oy,oz,dx,dy,dz,distance)

    cpdef bint Visible(self,double ax,double ay,double az,double bx,double by,double bz):
        cdef double dx=bx-ax,dy=by-ay,dz=bz-az,d=sqrt(dx*dx+dy*dy+dz*dz),inv
        if d<1e-6:return True
        inv=1./d
        return self.cast(ax,ay,az,dx*inv,dy*inv,dz*inv,d-.05)>=d-.05

    cpdef tuple NavCell(self, double x, double y, double step_up, double body_height):
        """Ground height, clearance, headroom, roof height, solid, highest surface."""
        cdef double g=self.sample(x,y), z=g, roof=-INFINITY, head=40., clear2=64.
        cdef int c=self.cell(x,y), pi,p,b,i,j,k,e,row,it
        cdef double top,base,ex,ey,l2,t,ddx,ddy,d2
        cdef bint changed
        for it in range(4):
            changed=False
            for pi in range(self.poff[c],self.poff[c+1]):
                p=self.pids[pi]
                top=self.prism[p*6+1];base=self.prism[p*6]
                if top<=g or base>g+.3 or not self.inside(p,x,y):continue
                if top-g<=step_up:g=top;changed=True
                else:roof=max(roof,<double>(<float>top))
            if not changed:break
        for pi in range(self.poff[c],self.poff[c+1]):
            p=self.pids[pi];top=self.prism[p*6+1]
            if top>z and self.inside(p,x,y):z=top
        if roof!=-INFINITY:
            for it in range(4):
                changed=False
                for pi in range(self.poff[c],self.poff[c+1]):
                    p=self.pids[pi];top=self.prism[p*6+1];base=self.prism[p*6]
                    if top>roof and base<=roof+.3 and self.inside(p,x,y):
                        roof=top;changed=True
                if not changed:break
            return 0,0,0,roof,1,z
        for pi in range(self.poff[c],self.poff[c+1]):
            p=self.pids[pi];base=self.prism[p*6]
            if base>=g+.3 and base-g<head and self.inside(p,x,y):head=base-g
        for j in range(bound(<int>((y-8-self.gy)/8),self.gny),bound(<int>((y+8-self.gy)/8),self.gny)+1):
            for i in range(bound(<int>((x-8-self.gx)/8),self.gnx),bound(<int>((x+8-self.gx)/8),self.gnx)+1):
                row=j*self.gnx+i
                for k in range(self.eoff[row],self.eoff[row+1]):
                    e=self.eids[k]*6
                    if g+body_height<=self.edges[e+4] or g+step_up+.05>=self.edges[e+5]:continue
                    ex=self.edges[e+2]-self.edges[e];ey=self.edges[e+3]-self.edges[e+1]
                    l2=ex*ex+ey*ey
                    t=0 if l2<1e-18 else max(0.,min(1.,((x-self.edges[e])*ex+(y-self.edges[e+1])*ey)/l2))
                    ddx=x-(self.edges[e]+ex*t);ddy=y-(self.edges[e+1]+ey*t)
                    d2=ddx*ddx+ddy*ddy
                    clear2=min(clear2,d2)
        return g,sqrt(clear2),head,float("nan"),0,z


from array import array
from libcpp.vector cimport vector
from libc.math cimport hypot

cdef struct Entry:
    int k
    float score

@final
cdef class Grid:
    cdef int nx,ny,generation
    cdef double x0,y0,wx0,wy0,wx1,wy1
    cdef float[:] z,clear,head,tops,travel
    cdef unsigned char[:] solid
    cdef int[:] parent,stamp,closed
    cdef vector[Entry] pending

    def __init__(self,nav):
        self.nx,self.ny,self.x0,self.y0=nav.NX,nav.NY,nav.MinX,nav.MinY
        self.wx0,self.wy0,self.wx1,self.wy1=nav.W.MinX,nav.W.MinY,nav.W.MaxX,nav.W.MaxY
        self.z,self.clear,self.head,self.tops,self.solid=nav.Z,nav.Clear,nav.Head,nav._tops,nav.Solid
        size=self.nx*self.ny
        self.travel=array("f",[0])*size;self.parent=array("i",[0])*size
        self.stamp=array("i",[0])*size;self.closed=array("i",[0])*size
        self.generation=0

    cdef inline bint walk(self,int k,double r,double h) noexcept:
        return not self.solid[k] and self.clear[k]>=r and self.head[k]>=h

    cpdef bint Walkable(self,int k,double r,double h):
        if k<0 or k>=self.nx*self.ny:return False
        return self.walk(k,r,h)

    cpdef int Index(self,double x,double y):
        return bound(<int>((y-self.y0)*.5),self.ny)*self.nx+bound(<int>((x-self.x0)*.5),self.nx)

    cpdef int Nearest(self,double x,double y,double r,double h,int maxR):
        cdef int ci=bound(<int>((x-self.x0)*.5),self.nx), cj=bound(<int>((y-self.y0)*.5),self.ny)
        cdef int rad,i,j,k,best=-1
        cdef double d,px,py,minimum=1e18
        for rad in range(maxR+1):
            for j in range(max(0,cj-rad),min(self.ny,cj+rad+1)):
                for i in range(max(0,ci-rad),min(self.nx,ci+rad+1)):
                    if abs(i-ci)!=rad and abs(j-cj)!=rad:continue
                    k=j*self.nx+i
                    if not self.walk(k,r,h):continue
                    px=self.x0+(i+.5)*2-x;py=self.y0+(j+.5)*2-y;d=px*px+py*py
                    if d<minimum:minimum=d;best=k
            if best>=0:return best
        return -1

    cpdef bint WalkLine(self,double ax,double ay,double bx,double by,double r,double h):
        cdef int steps=<int>hypot(bx-ax,by-ay)+1,prev=self.Index(ax,ay),i,k
        cdef double t
        if not self.walk(prev,r,h):return False
        for i in range(1,steps+1):
            t=(<double>i)/steps;k=self.Index(ax+(bx-ax)*t,ay+(by-ay)*t)
            if k==prev:continue
            if not self.walk(k,r,h) or self.z[k]-self.z[prev]>1.19*2*.85:return False
            prev=k
        return True

    cdef inline void push(self,int k,float score):
        cdef Entry entry
        cdef int i=self.pending.size(),p
        entry.k=k;entry.score=score;self.pending.push_back(entry)
        while i>0:
            p=(i-1)//2
            if self.pending[p].score<=score:break
            self.pending[i]=self.pending[p];i=p
        self.pending[i]=entry

    cdef inline int pop(self) noexcept:
        cdef int n=self.pending.size()-1,top=self.pending[0].k,i=0,l,m
        cdef Entry last=self.pending[n]
        self.pending.pop_back()
        if n:
            while True:
                l=2*i+1
                if l>=n:break
                m=l
                if l+1<n and self.pending[l+1].score<self.pending[l].score:m=l+1
                if last.score<=self.pending[m].score:break
                self.pending[i]=self.pending[m];i=m
            self.pending[i]=last
        return top

    cdef inline float heuristic(self,int k,int gi,int gj,double weight) noexcept:
        cdef int di=abs(k%self.nx-gi), dj=abs(k//self.nx-gj)
        return (max(di,dj)+.4142*min(di,dj))*2.*weight

    cpdef list PathTo(self,int k):
        cdef list path=[]
        while k>=0:
            path.append(k);k=self.parent[k]
            if len(path)>100000:break
        path.reverse()
        return path

    cpdef search(self,int mode,double sx,double sy,double tx,double ty,double r,double h,int maxexpand,double maxcost,extra,visit,double sz,double climb):
        """Mode 0 runs ground A*, 1 runs a flood and 2 runs rooftop A*."""
        cdef int start,goal=0,gi=0,gj=0,ci,cj,i,j,d,nk,k,expanded=0,bk
        cdef int[8] di=[1,-1,0,0,1,1,-1,-1]
        cdef int[8] dj=[0,0,1,-1,1,-1,1,-1]
        cdef double dist,hcur,dh,x,y,surfacecost,weight=1.1 if mode==2 else 1.15
        cdef float bh,hh,cost,ng,want=r+2,up
        if mode==2:
            start=self.Index(sx,sy);goal=self.Index(tx,ty)
        else:
            start=self.Nearest(sx,sy,r,h,6)
            if mode==0:goal=self.Nearest(tx,ty,r,h,10)
        if start<0 or goal<0:return [] if mode!=1 else None
        if mode!=1:
            if start==goal:return [start]
            gi=goal%self.nx;gj=goal//self.nx
        self.generation+=1
        cdef int gen=self.generation
        self.pending.clear();self.stamp[start]=gen;self.travel[start]=0;self.parent[start]=-1
        bk=start;bh=self.heuristic(start,gi,gj,weight) if mode!=1 else 0
        self.push(start,bh)
        while self.pending.size():
            k=self.pop()
            if self.closed[k]==gen:continue
            self.closed[k]=gen
            if mode==1:
                if not visit(k,self.travel[k]):return
            else:
                if k==goal:bk=goal;break
                expanded+=1
                if expanded>maxexpand:break
                hh=self.heuristic(k,gi,gj,weight)
                if hh<bh:bh=hh;bk=k
            ci=k%self.nx;cj=k//self.nx
            hcur=sz if k==start else self.tops[k]
            for d in range(8):
                i=ci+di[d];j=cj+dj[d]
                if i<0 or j<0 or i>=self.nx or j>=self.ny:continue
                nk=j*self.nx+i
                if self.closed[nk]==gen:continue
                dist=2.82842712 if d>=4 else 2.
                if mode==2:
                    x=self.x0+i*2+1;y=self.y0+j*2+1
                    if x<self.wx0 or x>self.wx1 or y<self.wy0 or y>self.wy1:continue
                    if extra is not None and extra(nk):continue
                    dh=self.tops[nk]-hcur;surfacecost=dist
                    if dh>climb:continue
                    elif dh>1.2:surfacecost+=10+dh*2.2
                    elif dh<-1.2:surfacecost+=1.5
                    if not self.solid[nk] and self.clear[nk]<r-.3:surfacecost+=14
                    cost=surfacecost
                else:
                    if not self.walk(nk,r,h):continue
                    if d>=4 and (not self.walk(cj*self.nx+i,r,h) or not self.walk(j*self.nx+ci,r,h)):continue
                    up=self.z[nk]-self.z[k]
                    if up>1.19*dist*.85:continue
                    cost=dist
                    if mode==0 and self.clear[nk]<want:cost+=<float>((want-self.clear[nk])*<float>.6)
                    if extra is not None:cost+=<float>extra(nk)
                ng=self.travel[k]+cost
                if mode==1 and ng>maxcost:continue
                if self.stamp[nk]!=gen or ng<self.travel[nk]:
                    self.stamp[nk]=gen;self.travel[nk]=ng;self.parent[nk]=k
                    hh=0 if mode==1 else self.heuristic(nk,gi,gj,weight)
                    self.push(nk,ng+hh)
        if mode==1:return
        return [] if bk==start else self.PathTo(bk)
