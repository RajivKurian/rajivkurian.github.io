"""Trace educational RTL excerpts to the frozen generated circuit graph."""
import re

# Decode only the wire types used by the frozen Circuit message. No research
# tool or generated protobuf module is needed to prepare the article.
def fields(blob):
    result={}; pos=0
    def varint():
        nonlocal pos
        value=shift=0
        while True:
            byte=blob[pos];pos+=1;value|=(byte&127)<<shift
            if byte<128:return value
            shift+=7
    while pos<len(blob):
        tag=varint(); key,kind=tag>>3,tag&7
        if kind==0:value=varint()
        elif kind==2:
            size=varint();value=blob[pos:pos+size];pos+=size
        else:raise ValueError(f'Unexpected protobuf wire type {kind}')
        result.setdefault(key,[]).append(value)
    return result

def packed(values):
    out=[]
    for value in values:
        if isinstance(value,int):out.append(value);continue
        pos=0
        while pos<len(value):
            n=shift=0
            while True:
                b=value[pos];pos+=1;n|=(b&127)<<shift
                if b<128:break
                shift+=7
            out.append(n)
    return out

def load(blob,rtl):
    f=fields(blob); gates={}
    for raw in f[3]:
        g=fields(raw);get=lambda n,default=0:g.get(n,[default])[0]
        stage=get(4);stage=(stage>>1)^-(stage&1)
        gates[get(1)]={'id':get(1),'op':get(2),'args':packed(g.get(3,[])), 'stage':stage,'live':bool(get(8)), 'group':get(5,b'').decode(),'bit':get(6)}
    signals={}
    for raw in f[4]:
        s=fields(raw);signals[s[1][0].decode()]=packed(s.get(3,[]))
    heaps=[]
    for raw in f[5]:
        h=fields(raw);heaps.append([packed(fields(r).get(1,[])) for r in h[4]])
    lines=rtl.splitlines(); source={}
    for number,line in enumerate(lines,1):
        m=re.match(r'assign n(\d+) =|  n(\d+) <=',line)
        if m:source[int(m[1] or m[2])]={'line':number,'text':line.strip()}
    return gates,signals,heaps,source

def cone(gates,roots,stop=None):
    found=set();pending=list(roots)
    while pending:
        i=pending.pop()
        if i<2 or i in found:continue
        g=gates[i]
        if stop and stop(g):continue
        found.add(i);pending.extend(g['args'])
    return found

def replay(gates, rows, column, limit=0):
    lookup={(g['op'],tuple(g['args'])):i for i,g in gates.items()}
    def op(kind,a,b=0):
        if kind==6:
            if a<2:return 1-a
            if gates[a]['op']==6:return gates[a]['args'][0]
            args=(a,)
        else:
            a,b=sorted((a,b))
            if kind==4:
                if a==0:return 0
                if a==1 or a==b:return b
            if kind==5:
                if a==0 or a==b:return b
                if a==1:return 1
            if kind==3:
                if a==b:return 0
                if a==0:return b
                if a==1:return op(6,b)
            args=(a,b)
        return lookup[(kind,args)]
    def fa(a,b,c):
        p=op(3,a,b)
        return op(3,p,c),op(5,op(4,a,b),op(4,p,c))
    layers=[];sample=None;width=len(rows[0])
    while len(rows)>2:
        before=rows;groups=[]
        if column:
            cols=[[] for _ in range(width)]
            for j in range(width):
                bits=[r[j] for r in rows if r[j]!=0];i=0
                while i+2<len(bits):
                    triple=bits[i:i+3];s,c=fa(*triple)
                    if s:cols[j].append(s)
                    if c and j+1<width:cols[j+1].append(c)
                    groups.append((j,triple,s,c));i+=3
                cols[j].extend(bits[i:])
            height=max(2,max(map(len,cols)));rows=[[0]*width for _ in range(height)]
            for j,col in enumerate(cols):
                for i,b in enumerate(col):rows[i][j]=b
        else:
            rows=[];i=0
            while i+2<len(before):
                sums=[];carries=[0]*width
                for j in range(width):
                    triple=[before[i+k][j] for k in range(3)];s,c=fa(*triple);sums.append(s)
                    if j+1<width:carries[j+1]=c
                    groups.append((j,triple,s,c))
                rows += [sums,carries];i+=3
            rows.extend(before[i:])
        layers.append({'rows':len(rows),'live_positions':sum(b>1 for r in rows for b in r)})
        if sample is None:
            sample=next((g for g in groups if g[0]==4),None)
            if sample is None:
                sample=next((g for g in groups if g[3]>1 and gates[g[3]]['live']),None)
        if limit and len(layers)>=limit:break
    return layers,sample,rows

def source_excerpt(ids,source,limit=18):
    entries=[source[i] for i in sorted(ids) if i in source]
    shown=entries[:limit]
    return '\n'.join(f"{e['line']:5}  {e['text']}" for e in shown), '\n'.join(f"{e['line']:5}  {e['text']}" for e in entries)

def carry_aliases(gates,leaves,constant_rows):
    """Recognize P/G expressions from exact row inputs and Boolean equations."""
    lookup={(g['op'],tuple(g['args'])):i for i,g in gates.items()}
    def find(kind,a,b):
        a,b=sorted((a,b))
        if kind==3:
            if a==b:return 0
            if a==0:return b
        if kind==4:
            if a==0:return 0
            if a==1 or a==b:return b
        return lookup.get((kind,(a,b)))
    rows={}
    for r,row in enumerate(constant_rows[:2]):
        for bit,value in enumerate(row):
            if value<2:rows.setdefault(bit,{})[r]=value
    for i,label in leaves.items():
        m=re.fullmatch(r'row([01])(?:_r\d+)?\[(\d+)\]',label)
        if m:rows.setdefault(int(m[2]),{})[int(m[1])]=i
    P={};G={};terms={};aliases={}
    for bit,row in rows.items():
        if 0 not in row or 1 not in row:continue
        a,b=row[0],row[1]
        for target,kind in [(P,3),(G,4)]:
            result=find(kind,a,b)
            if result is not None and result>1:target[result]=(bit,bit)
    def joined(high,low):
        return (high[0],low[1]) if high[1]==low[0]+1 else None
    for i,g in sorted(gates.items()):
        if g['op'] in (4,5):
            a,b=g['args']
            if g['op']==4:
                if a in P and b in P:
                    span=joined(P[a],P[b]) or joined(P[b],P[a])
                    if span:P[i]=span
                for x,y in [(a,b),(b,a)]:
                    if x in P and y in G:
                        span=joined(P[x],G[y])
                        if span:terms[i]=(P[x],G[y],span)
            else:
                for x,y in [(a,b),(b,a)]:
                    if x in G and y in terms and G[x]==terms[y][0]:G[i]=terms[y][2]
        for target,label in [(P,'propagate'),(G,'generate')]:
            if i in target:
                hi,lo=target[i];aliases[i]=f'{label}_{hi}' if hi==lo else f'{label}_{hi}_{lo}'
        if i in terms:
            hi,lo=terms[i][2];aliases[i]=f'propagated_carry_{hi}_{lo}'
    # A simplified expression can implement more than one group. IDs remain
    # unique display aliases; retain a suffix if two expressions share a span.
    used={}
    for i,label in list(aliases.items()):
        if label in used:aliases[i]=f'{label}_node{i}'
        used[aliases[i]]=i
    return {i:label for i,label in aliases.items() if i not in leaves}

def readable(gates,source,roots,leaves,root_names,focused=False,constant_rows=()):
    ids=cone(gates,roots,lambda g:g['id'] in leaves or g['op'] in (2,7))
    names=dict(leaves)
    if focused:names.update(carry_aliases(gates,leaves,constant_rows))
    names.update(root_names);counter=0;out=[];origin=[]
    def name(i):return "1'b%d"%i if i<2 else names.get(i,f'n{i}')
    for i in sorted(ids):
        if i not in names:
            counter+=1
            names[i]=f'{ {3:"xor",4:"and",5:"or",6:"invert"}[gates[i]["op"]]}_term_{counter}'
            if focused:
                args=gates[i]['args']
                labels=[names.get(a,'') for a in args]
                positions=[re.search(r'row\d+(?:_r\d+)?\[(\d+)\]',label) for label in labels]
                if len(args)==2 and all(positions) and positions[0][1]==positions[1][1]:
                    bit=positions[0][1]
                    if gates[i]['op']==3:names[i]=f'propagate_{bit}'
                    elif gates[i]['op']==4:names[i]=f'generate_{bit}'
                elif gates[i]['op']==4 and all(label.startswith('propagate_') for label in labels):
                    bits=[int(v) for label in labels for v in re.findall(r'\d+',label)]
                    names[i]=f'propagate_{max(bits)}_{min(bits)}'
                elif gates[i]['op']==4 and any(label.startswith('propagate_') for label in labels):
                    names[i]=f'carry_term_{counter}'
                elif gates[i]['op']==5 and any(label.startswith(('generate_','carry_term_')) for label in labels):
                    names[i]=f'carry_group_{counter}' 
        g=gates[i]
        rhs=('~'+name(g['args'][0])) if g['op']==6 else (' '+{3:'^',4:'&',5:'|'}[g['op']]+' ').join(name(a) for a in g['args'])
        out.append(f'assign {name(i)} = {rhs};')
        assert i in source, f'Excerpt contains non-emitted gate {i}'
        ref=lambda bit: f"1'b{bit}" if bit<2 else f'n{bit}'
        raw_rhs=('~'+ref(g['args'][0])) if g['op']==6 else (' '+{3:'^',4:'&',5:'|'}[g['op']]+' ').join(ref(a) for a in g['args'])
        assert source[i]['text']==f'assign n{i} = {raw_rhs};'
        origin.append(source[i]['line'])
    if focused and len(out)>16:
        # Keep actual assignments nearest the selected output. Earlier aliases
        # are dependencies in the complete, separately expandable source cone.
        out=['// Final 16 assignments on this output cone.',
             '// Earlier row/group signals are defined in the complete source.']+out[-16:]
        origin=origin[-16:]
    if not out:
        for i,label in root_names.items():out.append(f'// {label} simplifies to {name(i)}.')
    return '\n'.join(out),origin

def build(record,k,blob,rtl):
    gates,signals,heaps,source=load(blob,rtl)
    spec=fields(blob);impl=fields(spec[2][0]);get=lambda d,n,v=0:d.get(n,[v])[0]
    latency=record.get('cycles',4)
    pipe=fields(get(impl,11,b''))
    operand=get(pipe,1,1);first_result=get(pipe,3,2 if latency==4 else 3)
    cuts=[get(pipe,2,1 if latency==4 else 2),get(pipe,4,3 if latency==4 else 4)]
    column=k['compression']=='COLUMN_GREEDY'
    shared=k['decode_storage']=='CARRIED';residual=k['recoding']=='RESIDUAL'
    early=int(k.get('compression_layers_before_cut',0))>0;low=k['resolve_low_columns']=='true'
    blocks={}
    # The ROM words are identical across implementation choices. Some builds
    # omit additional dead outputs; explain the packed live-output declaration.
    rom=re.search(r'reg \[\d+:0\] rom;.*?\nend\n',rtl,re.S).group()
    blocks['rom']={'title':'Coefficient ROM','choice':'Fixed fitted words','variant':'fixed','kind':'rom',
      'explanation':'The 256 coefficient rows are the same in these experiments. The producer packs only live variable bits into rom; common constants are literals in the consuming logic.',
      'code':'\n'.join(rom.splitlines()[:3]+['    // 256 fitted rows; expand the contents below.','  endcase','end']), 'full':rom,'origin':'sfu_poly.sv · coefficient lookup','changed':False}
    for index,heap in enumerate(heaps):
        number=index+1;stage=operand if index==0 else first_result;cut=cuts[index]
        mac=fields(get(impl,9+index,b''));high=fields(get(mac,2,b''));low_plan=fields(get(mac,1,b''))
        carry_kind=get(high,1,get(impl,6,1));prefix=carry_kind==2;hybrid=carry_kind==3
        unified=bool(get(mac,6));product_stage=get(mac,7,stage);early_layers=get(mac,8)
        prod=cone(gates,[b for r in heap for b in r],lambda g:g['op']==7 or g['op']==2)
        # Select a genuinely variable product position with a small explanatory cone.
        candidates=[b for r in heap[1:-2] for b in r if b>1 and gates[b]['live']]
        root=min(candidates,key=lambda b:abs(len(cone(gates,[b],lambda g:g['op'] in (2,7)))-7))
        leaves={}
        for i in cone(gates,[root]):
            g=gates[i]
            if g['op']==7:
                origin=i
                while gates[origin]['op']==7:origin=gates[origin]['args'][0]
                base=gates[origin]
                leaves[i]=f"{base['group'] if base['group']!='x' else 't'}_r{stage}[{base['bit']}]" if base['op']==2 else f'control_r{stage}_{i}'
            elif g['op']==2:leaves[i]=f"{g['group']}[{g['bit']}]"
        code,origins=readable(gates,source,[root],leaves,{root:'selected_product_bit'})
        if shared:prod |= {i for i,g in gates.items() if g['stage']==0 and g['live'] and g['op'] not in (2,7)}
        excerpt,full=source_excerpt(prod,source)
        if shared:
            decoder_root=next(i for i,g in gates.items() if g['stage']==0 and g['live'] and g['op']==4)
            input_aliases={i:f"t[{g['bit']}]" for i,g in gates.items() if g['op']==2 and g['group']=='x'}
            decoder_code,decoder_origins=readable(gates,source,[decoder_root],input_aliases,{decoder_root:'shared_digit_two'})
            code='// Shared decoder before R1\n'+decoder_code+'\n\n// Product selection after the controls arrive\n'+code
            origins+=decoder_origins
        recoded='t' if residual else ('a' if index==0 else 's')
        blocks[f'product{number}']={'title':f'{"a × t" if index==0 else "s × t"}: Booth products','choice':f'Recode {recoded} · '+('carried controls' if shared else 'local decoder'), 'variant':'shared' if shared else 'residual' if residual else 'narrow','kind':'product',
          'explanation':f'This multiplier recodes {recoded}. '+('The decoder runs before R1, and its controls travel to this stage.' if shared else 'Its decoder is local to this multiplier.')+' The excerpt follows one variable product bit through the actual selection logic.',
          'code':code,'full':full,'origin':f'sfu_poly.sv · selection cone, lines {min(origins)}–{max(origins)}','changed':residual or shared,
          'rows':10 if residual else (5 if index==0 else 8)}
        selected_heap=heap
        before_layers=[]
        if product_stage>stage:
            partial=heap
            if 8 in mac:before_layers,_,partial=replay(gates,heap,column,early_layers)
            early_layers=len(before_layers)
            lookup={(g['args'][0],g['stage']):i for i,g in gates.items() if g['op']==7}
            def delay(bit):
                while bit>1 and gates[bit]['stage']<product_stage:
                    bit=lookup[(bit,gates[bit]['stage']+1)]
                return bit
            selected_heap=[[delay(bit) for bit in row] for row in partial]
            regs={i for i,g in gates.items() if g['live'] and g['op']==7 and g['stage']==product_stage}
            excerpt,full=source_excerpt(regs,source,12)
            row_aliases={}
            for r,row in enumerate(partial):
                for j,bit in enumerate(row):
                    if bit>1:row_aliases.setdefault(bit,(r,j))
            assignments=[]
            for i in sorted(regs):
                value=gates[i]['args'][0]
                if value in row_aliases:
                    r,j=row_aliases[value]
                    assignments.append(f'  held_row{r}[{j}] <= '+('compressed' if early_layers else 'product')+f'_row{r}[{j}];')
            excerpt='always @(posedge clk) begin\n'+'\n'.join(assignments[:12])+'\nend'
            raw_positions={bit for row in heap for bit in row}
            pre_logic=cone(gates,[gates[i]['args'][0] for i in regs],
                           lambda g:g['id'] in raw_positions or g['op'] in (2,7))
            _,full=source_excerpt(regs|pre_logic,source)
            blocks[f'product_cut{number}']={'title':f'Compression + R{product_stage}' if early_layers else f'R{product_stage}: early row register',
                'choice':f'{early_layers} compression layers before storage','variant':'early','kind':'cut','complete_compression':len(partial)<=2,
                'explanation':('Compression finishes before the extra register, which holds the final two rows for carry completion.' if len(partial)<=2 else 'The extra register holds '+('partially compressed rows' if early_layers else 'selected product rows and the aligned coefficient')+' before the remaining compression.')+f' {early_layers} compressor layers precede it. The excerpt shows the bank assignments; expanded source also includes those compression layers. Constants and repeated signals share storage.',
                'code':excerpt,'full':full,'origin':f'sfu_poly.sv · R{product_stage} assignments',
                'changed':True,'bits':record['graph_register_bits_by_stage'][product_stage]}
        layers,sample,cut_rows=replay(gates,selected_heap,column,1 if early else 0)
        if sample is not None:
            col,triple,s,c=sample
            labels=['b' if index==0 else 'c']+[f'd{i}' for i in range(len(heap)-3)]+['correction','bias']
            leaves={b:(f'{labels[r]}_aligned[{j}]' if selected_heap is heap else f'held_row{r}[{j}]') for r,row in enumerate(selected_heap) for j,b in enumerate(row) if b>1}
            code,origins=readable(gates,source,[s,c],leaves,{s:f'sum_bit_{col}',c:f'carry_bit_{col+1}'})
            relevant=cone(gates,signals['s'] if index==0 else signals['y'],lambda g:g['stage']<stage or (g['op']==7 and g['stage']==stage))
            compression=cone(gates,[bit for row in cut_rows for bit in row],lambda g:g['id'] in prod or g['op'] in (2,7))
            compression={i for i in compression if gates[i]['stage']==product_stage}
            _,full=source_excerpt(compression,source,100)
            blocks[f'compress{number}']={'title':f'Multiply-add {number}: compression','choice':'Column grouping' if column else 'Whole-row grouping','variant':'columns' if column else 'rows','kind':'compression','layers':layers,'initial_rows':len(heap),
              'explanation':('Column grouping takes d0, d1 and d2 at weight 4, so one compressor combines all three.' if column else f'Whole-row grouping takes {labels[0]}, d0 and d1. At weight 4 the coefficient contributes zero; d2 waits for another group.')+' The highlighted assignments implement this column. Sum stays at weight 4; carry enters weight 5.',
              'code':code,'full':full,'origin':f'sfu_poly.sv · column 4 cone, lines {min(origins)}–{max(origins)}','changed':column,'inputs':['d0[4]','d1[4]','d2[4]'] if column else ['0','d0[4]','d1[4]']}
            blocks[f'compress{number}']['column']=col
            if product_stage>stage:
                blocks[f'compress{number}'].update(
                    explanation=f'The rows have crossed R{product_stage} after {early_layers} earlier compression layers. This compressor combines three remaining bits at weight {col}; sum stays here and carry moves to weight {col+1}.',
                    origin=f'sfu_poly.sv · remaining compression, lines {min(origins)}–{max(origins)}',
                    inputs=[f'held bit {i}' for i in range(3)])
        regs={i for i,g in gates.items() if g['live'] and g['op']==7 and g['stage']==cut}
        _,full=source_excerpt(regs,source)
        positions={bit:f'row{r}[{j}]' for r,row in enumerate(cut_rows) for j,bit in enumerate(row) if bit>1}
        computation_regs=regs & relevant
        carry_regs=[i for i in computation_regs if gates[i]['args'][0] not in positions]
        carry_id=min(carry_regs) if low and carry_regs else None
        if carry_id is not None:
            carry_logic=cone(gates,[gates[carry_id]['args'][0]],lambda g:g['id'] in positions or g['op'] in (2,7))
            _,full=source_excerpt(regs|carry_logic,source)
        assignments=[];register_aliases={}
        for i in sorted(computation_regs):
            value=gates[i]['args'][0]
            if value in positions:
                input_name=positions[value]
                output_name=input_name.replace('[',f'_r{cut}[')
                assignments.append(f'  {output_name} <= {input_name};')
                register_aliases[i]=output_name
            elif i==carry_id:
                assignments.append(f'  low_carry_r{cut} <= low_sum_carry;')
                register_aliases[i]=f'low_carry_r{cut}'
        # These names are display aliases for the exact saved register equations.
        code='always @(posedge clk) begin\n'+'\n'.join(assignments[:10])+'\nend'
        if cut==stage:
            # The first MAC has no internal register. Show the same exact
            # compressed row bits entering its combinational carry network.
            ids={bit for row in cut_rows for bit in row if bit>1 and gates[bit]['live']
                 and gates[bit]['op'] not in (2,7)}
            code,full=source_excerpt(ids,source,10)
        blocks[f'cut{number}']={'title':f'R{cut}: compression cut','choice':'Early heap cut' if early else 'Resolve low columns' if low else 'Full row storage','variant':'early' if early else 'resolved' if low else 'full','kind':'cut',
          'explanation':('One compression layer runs before this cut. Remaining rows cross the register and are compressed afterward.' if early else 'The discarded low columns are added before storage. Only their carry and the upper pair cross this cut.' if low else 'Both compressed rows cross this cut. Their low columns are still present and must be added in the next cycle.')+' The bank count also includes carried operands and valid bits.',
          'code':code,'full':full,'origin':f'sfu_poly.sv · R{cut} register assignments · local row aliases','changed':early or not low or column,'bits':record['graph_register_bits_by_stage'][cut]}
        if cut==stage:
            blocks[f'cut{number}'].update(title='First MAC: combinational boundary',
                choice='No internal register', kind='boundary', variant='fixed',
                explanation=f'This multiply-add completes between R{stage} and R{first_result}. These compressed row signals feed carry completion directly; no intermediate bank stores them.',
                origin='sfu_poly.sv · compressed signals before carry completion')
            del blocks[f'cut{number}']['bits']
        elif 3 in mac:
            resolved=get(mac,3)
            blocks[f'cut{number}'].update(choice=f'Resolve {resolved} low columns',
                explanation=f'This cut completes columns 0–{resolved-1} and stores their carry plus the unfinished upper rows. Numerical truncation still discards 17 columns after completing the sum; the cut and narrowing boundary are independent.')
        # Follow the most significant retained sum, rather than selecting an
        # arbitrary small XOR cone that may miss the changed carry network.
        roots=[]
        for bit in signals['s'] if index==0 else signals['y']:
            while bit>1 and gates[bit]['op']==7:bit=gates[bit]['args'][0]
            if bit>1:roots.append(bit)
        chosen=roots[-1]
        leaves={**positions,**register_aliases}
        for i in cone(gates,[chosen]):
            if gates[i]['op']==7 and i not in leaves:leaves[i]=f'held_bit_{i}'
        excerpt,origin=readable(gates,source,[chosen],leaves,{chosen:'completed_sum_bit'},focused=True,constant_rows=cut_rows)
        completion=cone(gates,roots,lambda g:g['id'] in leaves or g['op'] in (2,7))
        _,full=source_excerpt(completion,source)
        blocks[f'carry{number}']={'title':f'Multiply-add {number}: carry completion','choice':f'Ripple {get(high,2)} + prefix' if hybrid else 'Parallel prefix' if prefix else 'Ripple carry','variant':'hybrid' if hybrid else 'prefix' if prefix else 'ripple','kind':'carry',
          'explanation':(f'The low {get(high,2)} columns ripple; a prefix network completes the upper suffix.' if hybrid else 'Prefix completion combines generate/propagate groups with increasing strides.' if prefix else 'Ripple completion passes each carry to the next bit position.')+(' One network spans discarded and retained columns, because there is no internal register.' if unified else '')+(' Remaining compression is also after the cut in this experiment.' if early else '')+' The excerpt shows the final assignments feeding one retained sum bit.',
          'code':excerpt,'full':full,'origin':f'sfu_poly.sv · carry cone, lines {min(origin)}–{max(origin)}','changed':prefix or hybrid or early}
    regs={i for i,g in gates.items() if g['live'] and g['op']==7 and g['stage']==latency}
    excerpt,full=source_excerpt(regs,source,8)
    blocks['output']={'title':'Retained result and output','choice':f'25 bits · truncation · R{latency}','variant':'fixed','kind':'output', 'explanation':f'The numerical format and final internal truncation are fixed. R{latency} captures the completed result. Reset controls the output and valid chain.', 'code':excerpt,'full':full,'origin':'sfu_poly.sv · output registers','changed':False}
    return blocks
