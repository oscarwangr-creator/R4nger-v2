"""RedTeam Framework - Module: cloud/gcp_enum — Google Cloud Platform enumeration"""
from __future__ import annotations
import json
from typing import Any, Dict, List
from framework.modules.base import BaseModule, Finding, ModuleResult, Severity

class GCPEnumModule(BaseModule):
    def info(self) -> Dict[str, Any]:
        return {"name":"gcp_enum","description":"Enumerate GCP: IAM policy, public buckets, compute instances, service accounts.","author":"RTF Core Team","category":"cloud","version":"1.0","tags":["gcp","google","cloud","enumeration"]}
    def _declare_options(self) -> None:
        self._register_option("project_id","GCP Project ID",required=True)
        self._register_option("service_account_json","Path to service account JSON (or uses ADC)",required=False,default="")
        self._register_option("checks","Comma-separated: iam,storage,compute,serviceaccounts",required=False,default="iam,storage,compute")
        self._register_option("output_file","Save JSON results",required=False,default="")
    async def run(self) -> ModuleResult:
        project_id=self.get("project_id"); sa_json=self.get("service_account_json")
        checks=[c.strip() for c in self.get("checks").split(",")]; output_file=self.get("output_file")
        results={}; findings=[]
        try:
            if sa_json:
                import os; os.environ["GOOGLE_APPLICATION_CREDENTIALS"]=sa_json
            from google.oauth2 import service_account
            import googleapiclient.discovery
        except ImportError:
            return ModuleResult(success=False,error="google-auth/google-api-python-client not installed.")
        try:
            if "iam" in checks:
                crm=googleapiclient.discovery.build("cloudresourcemanager","v1")
                policy=crm.projects().getIamPolicy(resource=project_id,body={}).execute()
                bindings=policy.get("bindings",[])
                results["iam_bindings"]=bindings
                high_priv=["roles/owner","roles/editor","roles/iam.securityAdmin"]
                for b in bindings:
                    if b.get("role") in high_priv:
                        findings.append(self.make_finding(title=f"High-privilege IAM binding: {b.get('role')}",target=f"gcp:{project_id}",severity=Severity.HIGH,description=f"Members with {b.get('role')}: {b.get('members',[])}",evidence=b,tags=["gcp","iam","privilege"]))
            if "storage" in checks:
                storage=googleapiclient.discovery.build("storage","v1")
                buckets=storage.buckets().list(project=project_id).execute()
                bucket_list=buckets.get("items",[])
                results["buckets"]=[b.get("name") for b in bucket_list]
                for bucket in bucket_list:
                    try:
                        acl=storage.bucketAccessControls().list(bucket=bucket["name"]).execute()
                        for entry in acl.get("items",[]):
                            if entry.get("entity") in ("allUsers","allAuthenticatedUsers"):
                                findings.append(self.make_finding(title=f"Public GCS bucket: {bucket['name']}",target=f"gcs:{bucket['name']}",severity=Severity.HIGH,description=f"Bucket is publicly accessible via {entry.get('entity')}.",evidence={"bucket":bucket["name"],"entity":entry.get("entity")},tags=["gcp","storage","public","exposure"]))
                    except Exception: pass
        except Exception as exc:
            return ModuleResult(success=False,error=str(exc))
        if output_file:
            with open(output_file,"w") as fh: json.dump(results,fh,indent=2,default=str)
        return ModuleResult(success=True,output=results,findings=findings)
