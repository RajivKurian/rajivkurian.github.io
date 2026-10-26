"""Carry networks consume staggered compressor outputs; high bits stay left."""
import zipfile
from pathlib import Path
from draw_cost_diagrams import Diagram
from rtl_viewer_blocks import load,replay

BLUE,RUST,GRAY,AMBER='#356c92','#af5137','#75828a','#9a681c'
ROOT=Path(__file__).resolve().parents[1]

def box(d,x,y,w,h,labels,color=BLUE,size=15):
    d.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" fill="#f5f1e8" stroke="{color}" stroke-width="1.5"/>')
    for j,label in enumerate(labels):d.text(x+w/2,y+h/2+(j-(len(labels)-1)/2)*20+5,label,size=size)

def path(d,points,color=GRAY,dashed=False):
    d.parts.append(f'<path d="{points}" fill="none" stroke="{color}" stroke-width="1.7" marker-end="url(#arrow)"'+(' stroke-dasharray="4 3"' if dashed else '')+'/>')

def incoming(d,offset,top,step=105):
    # The four column-packing paths from the preceding exact toy circuit.
    # Depth ticks differ visually from the actual FA cells in the worked circuit.
    for i,depth in enumerate([0,1,2,2]):
        x=offset+380-i*step
        d.text(x,top-12,f'bit {i}',size=14)
        for level in range(depth):
            y=top+level*34
            color=RUST if depth==2 else BLUE
            d.parts.append(f'<path d="M{x-10} {y+10} H{x+10}" stroke="{color}" stroke-width="4"/>')
            if level:path(d,f'M{x} {y-12} V{y}',RUST)
        end=top+depth*34
        if depth:path(d,f'M{x} {end-12} V{top+106}',RUST if depth==2 else BLUE)
        else:path(d,f'M{x} {top} V{top+106}',BLUE)
        d.text(x,top+124,['p00, b0','s1, 0','s2, 0','p21, c3'][i],size=13)
    return [offset+380-i*step for i in range(4)]

def carry_example():
    d=Diagram(960,490,'Ripple and prefix fed by the same column-packed rows; high bits on the left, carry travels toward higher weights')
    d.text(480,26,'Complete U + V from the column-packing example',size=21)
    d.text(480,52,'Longest incoming compressor path per column · high bits left · low bits right',size=16)
    for offset,title in [(15,'Ripple'),(500,'Prefix')]:
        d.text(offset+220,84,title,size=20,color=BLUE)
        xs=incoming(d,offset,119)
        if offset==15:
            for i,x in enumerate(xs):
                box(d,x-27,280,54,35,['HA' if i<3 else 'FA'],BLUE,15)
                path(d,f'M{x} 249 V280')
                if i<3:
                    path(d,f'M{x-27} 298 H{xs[i+1]+27}',BLUE)
                    d.text((x+xs[i+1])/2,285,f'k{i+1}',size=12)
                path(d,f'M{x} 315 V351');d.text(x,371,f'z{i}',size=15)
            path(d,f'M{xs[3]-27} 298 H{offset+18} V351');d.text(offset+18,371,'z4',size=15)
            d.text(offset+220,417,'A carry can advance through early low bits',size=15)
            d.text(offset+220,440,'while later row bits are still being computed.',size=15)
        else:
            for x in xs:
                path(d,f'M{x} 249 V279')
                d.parts.append(f'<circle cx="{x}" cy="284" r="5" fill="{BLUE}"/>')
            for level,stride in enumerate([1,2]):
                yy=323+level*39
                for i,x in enumerate(xs):
                    path(d,f'M{x} {yy-34} V{yy-5}',GRAY)
                    if i>=stride:path(d,f'M{xs[i-stride]} {yy-34} L{x} {yy-5}',BLUE)
                    d.parts.append(f'<circle cx="{x}" cy="{yy}" r="5" fill="{BLUE}"/>')
            for i,x in enumerate(xs):d.text(x,389,f'k{i+1}',size=15)
            d.text(offset+220,417,'Combine generate/propagate groups.',size=15)
            d.text(offset+220,440,'Then zᵢ = Pᵢ XOR kᵢ; k₀ = 0.',size=15)
    d.text(480,478,'Short ticks count FAs on the longest incoming compressor path; they are not separate cells.',size=15)
    d.save('producer-carry-example.svg')

def hybrid_example():
    # Verify the simplified two-bit prefix, including the parallel carry-out.
    for u in range(8):
        for v in range(4):
            for b in range(4):
                p=lambda i,j: ((u>>i)&1)&((v>>j)&1)
                n=p(1,0)+p(0,1)+((b>>1)&1);s1,c2=n&1,n>>1
                n=p(2,0)+p(1,1)+c2;s2,c3=n&1,n>>1
                n=p(0,0)+(b&1);z0,k1=n&1,n>>1
                n=s1+k1;z1,k2=n&1,n>>1
                P3=p(2,1)^c3;G3=p(2,1)&c3
                P32=P3&s2;k3=s2&k2;k4=G3|(P32&k2)
                z2=s2^k2;z3=P3^k3
                assert z0+2*z1+4*z2+8*z3+16*k4==u*v+b
    d=Diagram(900,715,'Connected hybrid network: incoming compressor paths above each column, ripple in bits zero and one, prefix in bits two and three')
    d.text(450,27,'Hybrid · ripple in bits 1–0, prefix in bits 3–2',size=22)
    xs=incoming(d,340,68,180)
    def dot(x,y,color=RUST):
        d.parts.append(f'<circle cx="{x}" cy="{y}" r="5" fill="{color}"/>')
    # Every column retains its horizontal position from the incoming paths.
    for x in xs:path(d,f'M{x} 198 V240')
    for x in [540,720]:
        box(d,x-30,240,60,40,['HA'],BLUE,17)
        path(d,f'M{x} 280 V595',BLUE)
    path(d,'M690 260 H570',BLUE);d.text(630,249,'k₁',size=15,color=BLUE)
    path(d,'M510 260 H475 V415 H145',BLUE)
    d.text(463,398,'k₂',size=16,color=BLUE)
    # Initial generate/propagate pairs and the one upper prefix combine.
    for x in [180,360]:
        dot(x,240)
        path(d,f'M{x} 245 V325',RUST)
        dot(x,330)
    path(d,'M360 245 L180 325',RUST)
    d.text(170,273,'G₃, P₃',size=14,anchor='end')
    d.text(432,293,'G₂ = 0',size=13,anchor='start')
    d.text(432,314,'P₂ = s2',size=13,anchor='start')
    d.text(168,350,'G₃:₂, P₃:₂',size=14,anchor='end',color=RUST)
    # The low carry enters both upper carries in parallel.
    for x,label in [(180,'G ∨ (P ∧ k₂)'),(360,'P₂ ∧ k₂')]:
        path(d,f'M{x} 335 V439',RUST)
        box(d,x-54,439,108,32,[label],RUST,13)
        path(d,f'M{x-35} 415 V439',BLUE)
        dot(x-35,415,BLUE)
    path(d,'M180 471 V490 H60 V595',RUST)
    d.text(85,486,'k₄',size=15,color=RUST)
    # Preserve each individual propagate bit for its sum XOR.
    path(d,'M180 240 H95 V551 H160',RUST)
    path(d,'M360 240 H420 V551 H380',RUST)
    d.text(107,521,'P₃',size=14,color=RUST)
    d.text(432,521,'P₂',size=14,color=RUST)
    path(d,'M360 471 V498 H200 V535',RUST)
    d.text(275,489,'k₃',size=14,color=RUST)
    path(d,'M440 415 V510 H340 V535',BLUE);dot(440,415,BLUE)
    for x in [180,360]:
        box(d,x-20,535,40,32,['⊕'],RUST,22)
        path(d,f'M{x} 567 V595',RUST)
    for x,label in [(60,'z4'),(180,'z3'),(360,'z2'),(540,'z1'),(720,'z0')]:
        d.text(x,616,label,size=18)
    d.text(450,645,'●  Generate/propagate pair     ↙  Combine adjacent groups',size=14)
    d.text(450,675,'Ticks above each column count its longest incoming FA path.',size=14)
    d.text(450,703,'The upper group produces k₄ directly from k₂, in parallel with k₃.',size=17)
    d.save('producer-hybrid-example.svg')

def prefix_node():
    d=Diagram(900,235,'One prefix node combines adjacent carry summaries without waiting for an incoming carry')
    d.text(450,25,'One prefix node combines two adjacent groups',size=21)
    for x,label in [(200,'Higher group · Gᴴ, Pᴴ'),(700,'Lower group · Gᴸ, Pᴸ')]:
        d.text(x,70,label,size=17)
        path(d,f'M{x} 83 L450 115',RUST)
    d.parts.append(f'<circle cx="450" cy="122" r="7" fill="{RUST}"/>')
    d.text(450,167,'G = Gᴴ OR (Pᴴ AND Gᴸ)     ·     P = Pᴴ AND Pᴸ',size=19)
    d.text(450,208,'The combined group generates a carry itself, or propagates a carry through both parts.',size=16)
    d.save('producer-prefix-node.svg')

def unified_example():
    d=Diagram(960,370,'Separate prefix groups pass a completed low carry to the upper half; unified groups cross the discard boundary')
    for offset,title,unified in [(0,'Separate low and upper networks',False),(480,'Unified prefix network',True)]:
        color=RUST if unified else BLUE
        d.text(offset+235,28,title,size=20,color=color)
        xs=[offset+415-i*100 for i in range(4)]
        for i,x in enumerate(xs):
            d.text(x,61,f'bit {i}',size=14)
            path(d,f'M{x} 72 V92')
            d.parts.append(f'<circle cx="{x}" cy="98" r="5" fill="{color}"/>')
            path(d,f'M{x} 103 V153',color)
            if i%2==1 or (unified and i>0):path(d,f'M{xs[i-1]} 103 L{x} 153',color)
            d.parts.append(f'<circle cx="{x}" cy="158" r="5" fill="{color}"/>')
        boundary=offset+265
        d.parts.append(f'<path d="M{boundary} 48 V312" stroke="{AMBER}" stroke-dasharray="4 4"/>')
        if unified:
            for i,x in enumerate(xs):
                path(d,f'M{x} 163 V235',color)
                if i>=2:path(d,f'M{xs[i-2]} 163 L{x} 235',color)
                d.parts.append(f'<circle cx="{x}" cy="240" r="5" fill="{color}"/>')
                path(d,f'M{x} 245 V282',color)
                d.text(x,304,f'k{i+1}',size=16)
            d.text(offset+235,337,'Groups cross the discard position.',size=17)
        else:
            # G[1:0] is k2 because the carry into bit zero is zero.
            path(d,f'M{xs[1]} 163 V212 H{offset+80}',BLUE)
            d.text(offset+352,203,'k₂',size=14,color=BLUE)
            for i in [2,3]:
                x=xs[i];path(d,f'M{x} 163 V238',BLUE)
                box(d,x-40,238,80,30,['G OR Pk₂'],BLUE,12)
                path(d,f'M{x-22} 212 V238',BLUE)
                d.parts.append(f'<circle cx="{x-22}" cy="212" r="3" fill="{BLUE}"/>')
                path(d,f'M{x} 268 V282',BLUE);d.text(x,304,f'k{i+1}',size=16)
            d.text(offset+235,337,'Upper carries consume the completed k₂.',size=17)
    d.text(480,365,'Same sum XORs and same truncation: discard z1, z0; keep z4, z3, z2.',size=16)
    d.save('producer-unified-example.svg')

def measured_example():
    import json
    # Arc delays and cell identities come from the formally traced mapped paths.
    z=zipfile.ZipFile(ROOT/'docs/artifacts/rtl-carry-audit.zip')
    data=json.loads((ROOT/'data/rtl-carry-audit.json').read_text())['comparison']
    d=Diagram(1000,390,'The actual mapped carry segment has four different cell arcs in prefix and hybrid implementations')
    d.text(500,27,'Same critical route: P₂₂ → carry c₃₀ → result s[14]',size=22)
    for y,r,color,title in [(82,data[0],BLUE,'Unified prefix'),(235,data[1],RUST,'Unified hybrid')]:
        trace=json.loads(z.read(r['name']+'/verified_trace.json'))
        start=next(i for i,a in enumerate(trace) if abs(a['time_ps']-r['p22_arrival_ps'])<.0001)
        arcs=trace[start+1:start+5]
        assert abs(sum(a['delay_ps'] for a in arcs)-r['p22_to_c30_ps'])<.001
        d.text(20,y,title,size=19,anchor='start',color=color)
        d.text(20,y+29,f'P₂₂ arrives: {r["p22_arrival_ps"]:.2f} ps',size=14,anchor='start')
        for i,a in enumerate(arcs):
            x=240+i*153
            short=a['type'].replace('_ASAP7_75t_R','')
            box(d,x,y-10,132,64,[short,f'{a["delay_ps"]:.2f} ps'],color,14)
            if i:path(d,f'M{x-21} {y+22} H{x}',color)
        path(d,f'M831 {y+22} H867',color)
        d.text(934,y+17,'c₃₀',size=17,color=color)
        d.text(934,y+40,f'{r["p22_to_c30_ps"]:.2f} ps later',size=13)
        d.text(525,y+81,f'Carry + remaining sum: {r["p22_to_c30_ps"]+r["c30_to_sum_ps"]:.2f} ps · s[14] arrives: {r["sum_arrival_ps"]:.2f} ps',size=15)
    d.text(500,374,'The hybrid starts this segment later, but its mapped cell arcs finish sooner.',size=17)
    d.save('producer-clock-carry.svg')

def register_cuts():
    # Independent signal sets at successive cuts in the complete toy circuit.
    bits={'p00','p10','p20','p01','p11','p21','b0','b1'}
    counts=[len(bits)]
    bits=(bits-{'p10','p01','b1'})|{'s1','c2'};counts.append(len(bits))
    bits=(bits-{'p20','p11','c2'})|{'s2','c3'};counts.append(len(bits))
    assert counts==[8,7,6]
    d=Diagram(930,335,'Three register positions in the same exact two-compressor circuit')
    d.text(465,25,'Move one register through the two dependent compressors',size=21)
    d.text(465,51,'Pipeline time → · unchanged wires bypass each compressor',size=15)
    for j,count in enumerate(counts):
        y=78+j*77
        d.text(20,y+25,f'{count} stored bits',size=17,anchor='start',color=[BLUE,AMBER,RUST][j])
        for x,label in [(290,'FA₁: p10 + p01 + b1'),(560,'FA₂: p20 + p11 + c2')]:
            box(d,x,y,225,43,[label],GRAY,15)
        path(d,f'M210 {y+22} H290');path(d,f'M515 {y+22} H560');path(d,f'M785 {y+22} H855')
        x=[245,537,820][j];color=[BLUE,AMBER,RUST][j]
        d.parts.append(f'<path d="M{x} {y-7} V{y+52}" stroke="{color}" stroke-width="5"/>')
    d.text(465,326,'Later cuts store fewer signals, but require more dependent work before the register.',size=16)
    d.save('producer-register-cuts.svg')

def draw_all():
    register_cuts();prefix_node();carry_example();hybrid_example();unified_example();measured_example()

if __name__=='__main__':
    draw_all();print('Drew consistent carry directions, incoming dependencies, unified completion and measured critical path.')
