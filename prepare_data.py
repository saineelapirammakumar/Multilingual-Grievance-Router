"""One-time annotation metadata for supplied demo corpus. No new evaluation examples."""
import sys,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit
from app.translation import normalize
# Semantic families manually reviewed across scripts: translations/paraphrases stay together.
GROUPS='''water_shortage water_shortage pipe_leak water_quality pipe_leak road_damage road_damage fallen_pole fallen_pole fallen_wire streetlight transformer hanging_power garbage_delay garbage_pile garbage_delay waste_burning drain_overflow sewage_street open_drain dirty_toilet drain_clean water_shortage pipe_leak garbage_pile garbage_delay road_damage fallen_pole fallen_wire streetlight drain_overflow sewage_street water_quality hanging_power garbage_delay water_shortage pipe_leak garbage_delay road_damage fallen_pole fallen_wire streetlight drain_overflow sewage_home water_quality garbage_bin pipe_leak water_shortage road_damage fallen_pole fallen_wire streetlight drain_overflow garbage_delay pipe_leak fallen_pole fallen_wire transformer sewage_home waste_burning low_pressure road_damage drain_clean garbage_delay streetlight water_tanker manhole open_manhole fallen_tree leaning_pole sparking_cable river_dump sewage_smell water_quality road_flood drain_overflow flood_home streetlight garbage_bin garbage_delay pipe_leak sewage_pipe road_damage road_damage fallen_wire fallen_wire fallen_pole'''.split()
def main():
    df=pd.read_csv(ROOT/'data/grievances.csv')
    assert len(df)==len(GROUPS),(len(df),len(GROUPS))
    df['row_id']=[f'orig-{i+1:03d}' for i in range(len(df))]
    df['group_id']=GROUPS
    df['language']=['Hinglish' if 22<=i<=34 else 'Tamil' if 35<=i<=46 else 'Tanglish' if 47<=i<=54 else 'English' for i in range(len(df))]
    df['provenance']='provided_demo_unverified_origin'
    df['synthetic_status']='unknown_treat_as_demonstration'
    df['original_urgency']=df.urgency
    # Preserve original annotations for reproducibility; flag rather than silently "fix" labels.
    flags={'water_shortage','pipe_leak','road_damage','fallen_pole','drain_clean','sewage_street','river_dump'}
    df['annotation_review_required']=df.group_id.isin(flags)
    train,test=next(GroupShuffleSplit(n_splits=1,test_size=.25,random_state=42).split(df,groups=df.group_id))
    df['split']='train';df.loc[test,'split']='test'
    df.to_csv(ROOT/'data/annotated.csv',index=False)
    report={'rows':len(df),'exact_duplicates':int(df.text.duplicated().sum()),'missing_cells':df[['text','departments','urgency']].isna().sum().to_dict(),
            'label_counts':df.departments.str.split('|').explode().value_counts().to_dict(),'urgency_counts':df.urgency.value_counts().to_dict(),
            'language_counts':df.language.value_counts().to_dict(),'split_counts':df.split.value_counts().to_dict(),
            'cross_split_groups':list(set(df[df.split=='train'].group_id)&set(df[df.split=='test'].group_id)),
            'annotation_flags':df[df.annotation_review_required][['row_id','group_id','urgency']].to_dict('records'),
            'limitations':'Manual group labels reduce obvious translation/paraphrase leakage; independent native-speaker adjudication and real held-out data are still needed.'}
    (ROOT/'reports/dataset_audit.json').write_text(json.dumps(report,indent=2))
    manifest={'seed':42,'train_ids':df[df.split=='train'].row_id.tolist(),'test_ids':df[df.split=='test'].row_id.tolist(),
              'dataset_sha256':hashlib.sha256((ROOT/'data/annotated.csv').read_bytes()).hexdigest(),'grouping':'manual issue families; no paraphrase augmentation'}
    (ROOT/'data/split_manifest.json').write_text(json.dumps(manifest,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main()
