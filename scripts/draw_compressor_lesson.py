"""Small complete multiply-add circuits for the compressor lesson."""
from draw_cost_diagrams import Diagram

BLUE, RUST, GRAY = '#356c92', '#af5137', '#75828a'

def rect(d,x,y,w,h,labels,color=GRAY,size=16):
    d.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" fill="#f5f1e8" stroke="{color}" stroke-width="1.5"/>')
    for i,label in enumerate(labels):d.text(x+w/2,y+h/2+(i-(len(labels)-1)/2)*21+5,label,size=size)

def path(d,points,color=GRAY):
    d.parts.append(f'<path d="{points}" stroke="{color}" stroke-width="1.5" fill="none" marker-end="url(#arrow)"/>')

def unit():
    d=Diagram(900,225,'A full adder compresses three equal-weight bits to a sum bit and a carry at twice the weight')
    d.text(450,25,'One 3:2 compressor is a full adder',size=21)
    for label,y in [('x',65),('y',100),('z',135)]:
        d.text(235,y+5,label,size=19);path(d,f'M255 {y} H355')
    rect(d,355,43,180,115,['full adder','3 inputs → 2 outputs'],BLUE,17)
    path(d,'M535 77 H635');d.text(655,83,'s · weight w',size=18,anchor='start')
    path(d,'M535 126 H635');d.text(655,132,'k · weight 2w',size=18,anchor='start')
    d.text(145,103,'each weight w',size=15)
    d.text(450,193,'x + y + z = s + 2k',size=21)
    d.save('producer-compressor-unit.svg')

def inputs():
    d=Diagram(900,215,'Six AND gates form a three-bit by two-bit product; the addend enters the same weighted columns')
    d.text(450,25,'u: 3 bits · v: 2 bits · b: 2 bits',size=20)
    xs=[370,510,650,790]
    for x,w in zip(xs,['8','4','2','1']):d.text(x,59,'weight '+w,size=15)
    rows=[('u × v₀',['0','p20','p10','p00']),('u × v₁ × 2',['p21','p11','p01','0']),('b',['0','0','b1','b0'])]
    for r,(name,bits) in enumerate(rows):
        y=90+r*37;d.text(240,y,name,size=17,anchor='end')
        for x,bit in zip(xs,bits):d.text(x,y,bit,size=19,color='#a3aaa9' if bit=='0' else BLUE if bit.startswith('p') else '#41484b')
    d.text(450,202,'pij = ui AND vj · each label is a signal bit, not a chosen value',size=16)
    d.save('producer-compressor-inputs.svg')

def gate(d,x,y,kind,ins,outs,color,serial=False,routed_carry=False):
    # Rectangular full/half-adder symbols with explicitly named nets.
    gx=x+145;w=76;h=72
    rect(d,gx,y,w,h,[kind],color,18)
    input_y=[y+18,y+54] if kind=='HA' else [y+12,y+36,y+60]
    for label,yy in zip(ins,input_y):
        if serial and label=='c2':continue
        d.text(x+90,yy+5,label,size=16,anchor='end')
        path(d,f'M{x+102} {yy} H{gx}',color)
    for output_index,(label,yy) in enumerate(zip(outs,[y+18,y+54])):
        if routed_carry and output_index==1:continue
        path(d,f'M{gx+w} {yy} H{x+260}',color)
        d.text(x+272,yy+5,label,size=16,anchor='start')

def final_adder(d,x,column,color):
    d.text(x+220,446,'Final carry-propagating addition',size=17)
    centers=[x+386-i*96 for i in range(4)]
    kinds=['HA','HA','HA','FA'] if column else ['wire','HA','FA','FA']
    operands=['p00, b0','s1','s2','p21, c3'] if column else ['s0','s1, c1','s2, c2','p21, c3']
    for i,(cx,kind,operand) in enumerate(zip(centers,kinds,operands)):
        d.text(cx,471,operand,size=13)
        if kind=='wire':
            path(d,f'M{cx} 481 V538',color)
        else:
            path(d,f'M{cx} 477 V493',color)
            rect(d,cx-26,493,52,32,[kind],color,15)
            path(d,f'M{cx} 525 V538',color)
            if i<3:path(d,f'M{cx-26} 509 H{centers[i+1]+26}',color)
            else:path(d,f'M{cx-26} 509 H{x+25} V538',color)
        d.text(cx,559,f'z{i}',size=16)
    d.text(x+25,559,'z4',size=16)

def circuits():
    d=Diagram(940,635,'Two complete compressor networks and final ripple adders for the same three-bit by two-bit multiply-add')
    for x,column,color,title in [(0,False,BLUE,'1 · Whole-row grouping'),(480,True,RUST,'2 · Column packing')]:
        d.text(x+230,26,title,size=21,color=color)
        if not column:
            gate(d,x+5,58,'HA',['p00','b0'],['s0','c1'],color)
            gate(d,x+5,158,'FA',['p10','p01','b1'],['s1','c2'],color)
            gate(d,x+5,243,'HA',['p20','p11'],['s2','c3'],color)
            d.text(x+365,103,'weight 1',size=14)
            d.text(x+365,203,'weight 2',size=14)
            d.text(x+365,288,'weight 4',size=14)
        else:
            gate(d,x+5,78,'FA',['p10','p01','b1'],['s1','c2'],color,routed_carry=True)
            gate(d,x+5,243,'FA',['p20','p11','c2'],['s2','c3'],color,True)
            # c2 is the actual third input of the next column's full adder.
            path(d,f'M{x+226} 132 H{x+405} V326 H{x+120} V303 H{x+150}',color)
            d.text(x+300,121,'c2',size=16)
            d.text(x+365,96,'weight 2',size=14)
            d.text(x+365,261,'weight 4',size=14)
        u='p21  s2  s1  p00' if column else 'p21  s2  s1  s0'
        v='c3    0    0   b0' if column else 'c3  c2  c1    0'
        rect(d,x+25,361,410,59,[f'U = [{u}]',f'V = [{v}]'],GRAY,15)
        d.text(x+230,351,'Two remaining rows · bits 3 … 0',size=14)
        final_adder(d,x,column,color)
        d.text(x+230,590,'Upstream FA/HA levels at bits 3 → 0: '+('2, 2, 1, 0' if column else '1, 1, 1, 1'),size=14,color=color)
        d.text(x+230,615,'2 dependent layers · 6 bits to store' if column else '1 parallel layer · 7 bits to store',size=15,color=color)
    d.parts.append('<path d="M468 10V620" stroke="#d9d5ca"/>')
    d.save('producer-compressor-circuits.svg')

def ha(a,b):return a^b,a&b

def fa(a,b,c):return a^b^c,(a&b)|(a&c)|(b&c)

def evaluate(u,v,b,column):
    p={(i,j):((u>>i)&1)&((v>>j)&1) for i in range(3) for j in range(2)}
    s1,c2=fa(p[1,0],p[0,1],(b>>1)&1)
    if column:
        s2,c3=fa(p[2,0],p[1,1],c2)
        U=(p[2,1]<<3)|(s2<<2)|(s1<<1)|p[0,0]
        V=(c3<<3)|(b&1)
        z0,k1=ha(p[0,0],b&1)
        z1,k2=ha(s1,k1);z2,k3=ha(s2,k2)
    else:
        s0,c1=ha(p[0,0],b&1);s2,c3=ha(p[2,0],p[1,1])
        U=(p[2,1]<<3)|(s2<<2)|(s1<<1)|s0
        V=(c3<<3)|(c2<<2)|(c1<<1)
        z0=s0;z1,k2=ha(s1,c1);z2,k3=fa(s2,c2,k2)
    z3,z4=fa(p[2,1],c3,k3)
    result=z0|(z1<<1)|(z2<<2)|(z3<<3)|(z4<<4)
    return U,V,result

def verify():
    for u in range(8):
        for v in range(4):
            for b in range(4):
                for column in [False,True]:
                    U,V,result=evaluate(u,v,b,column)
                    assert U+V==result==u*v+b,(u,v,b,column)

def draw_all():
    verify();unit();inputs();circuits()

if __name__=='__main__':
    draw_all();print('Drew the compressor unit, symbolic input columns and both complete circuits; checked all 128 inputs.')
