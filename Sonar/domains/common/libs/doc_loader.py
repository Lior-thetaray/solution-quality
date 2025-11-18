def get_doc(docpath):
    with open(f'/thetaray/git/solutions/{docpath}', 'r', encoding='utf-8') as f:
        text=f.read()
    return text
