from statistics import mean

def official_jump(jumps):
    values=sorted([float(x) for x in jumps],reverse=True)
    if len(values)!=3 or min(values)<=0: raise ValueError("Trois sauts valides sont obligatoires.")
    return round(mean(values[:2]),2)

def jump_variation(score,reference):
    if not reference: return None,None
    diff=round(score-reference,2)
    return diff,round(diff/reference*100,2)

def fatigue_status(diff_pct,orange=-5,red=-10):
    if diff_pct is None: return "Non disponible"
    if diff_pct<=red: return "Rouge"
    if diff_pct<=orange: return "Orange"
    return "Vert"

def estimated_1rm(load,reps):
    return round(float(load)*(1+int(reps)/30),1) if load and reps else 0.0
