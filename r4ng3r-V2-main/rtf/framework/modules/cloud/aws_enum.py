"""RedTeam Framework - Module: cloud/aws_enum"""
from __future__ import annotations
import json
from typing import Any, Dict, List
from framework.modules.base import BaseModule, Finding, ModuleResult, Severity

class AWSEnumModule(BaseModule):
    def info(self) -> Dict[str, Any]:
        return {"name":"aws_enum","description":"Enumerate AWS: IAM, S3, EC2, Lambda, public buckets, secrets. Uses boto3.","author":"RTF Core Team","category":"cloud","version":"1.2","tags":["aws","cloud","enumeration"]}
    def _declare_options(self) -> None:
        self._register_option("access_key_id","AWS Access Key ID",required=True)
        self._register_option("secret_access_key","AWS Secret Access Key",required=True)
        self._register_option("session_token","AWS Session Token (temp creds)",required=False,default="")
        self._register_option("region","AWS region",required=False,default="us-east-1")
        self._register_option("checks","Comma-separated: iam,s3,ec2,lambda,rds,secrets",required=False,default="iam,s3,ec2,lambda")
        self._register_option("output_file","Save findings to JSON",required=False,default="")
    async def run(self) -> ModuleResult:
        try:
            import boto3
        except ImportError:
            return ModuleResult(success=False,error="boto3 not installed. Run: pip install boto3")
        access_key=self.get("access_key_id"); secret_key=self.get("secret_access_key")
        session_token=self.get("session_token"); region=self.get("region")
        checks=[c.strip() for c in self.get("checks").split(",")]; output_file=self.get("output_file")
        session_kwargs={"aws_access_key_id":access_key,"aws_secret_access_key":secret_key,"region_name":region}
        if session_token: session_kwargs["aws_session_token"]=session_token
        session=boto3.Session(**session_kwargs)
        results={}; findings=[]
        try:
            sts=session.client("sts"); identity=sts.get_caller_identity()
            account_id=identity.get("Account","?"); arn=identity.get("Arn","?")
            results["identity"]={"account":account_id,"arn":arn}
            self.log.info(f"AWS Identity: {arn}")
            findings.append(self.make_finding(title=f"AWS credentials valid — Account: {account_id}",target="aws",severity=Severity.INFO,description=f"ARN: {arn}",evidence=results["identity"],tags=["aws","identity"]))
        except Exception as exc:
            return ModuleResult(success=False,error=f"STS identity check failed: {exc}")
        if "iam" in checks:
            try:
                iam=session.client("iam")
                users=iam.list_users().get("Users",[]); results["iam_users"]=[u["UserName"] for u in users]
                if users:
                    findings.append(self.make_finding(title=f"IAM: {len(users)} user accounts",target="aws:iam",severity=Severity.MEDIUM,description="IAM users enumerated.",evidence={"users":results["iam_users"]},tags=["aws","iam"]))
            except Exception as exc: self.log.warning(f"IAM enum error: {exc}")
        if "s3" in checks:
            try:
                s3=session.client("s3"); buckets=s3.list_buckets().get("Buckets",[])
                results["s3_buckets"]=[b["Name"] for b in buckets]
                if buckets:
                    findings.append(self.make_finding(title=f"S3: {len(buckets)} buckets",target="aws:s3",severity=Severity.MEDIUM,description="S3 buckets enumerated. Check for public access.",evidence={"buckets":results["s3_buckets"]},tags=["aws","s3"]))
                for bn in results["s3_buckets"][:15]:
                    try:
                        acl=s3.get_bucket_acl(Bucket=bn)
                        for grant in acl.get("Grants",[]):
                            if grant.get("Grantee",{}).get("URI","").endswith("AllUsers"):
                                findings.append(self.make_finding(title=f"PUBLIC S3 bucket: {bn}",target=f"aws:s3:{bn}",severity=Severity.HIGH,description="Bucket publicly accessible via AllUsers ACL.",evidence={"bucket":bn},tags=["aws","s3","public","exposure"]))
                    except Exception: pass
            except Exception as exc: self.log.warning(f"S3 enum error: {exc}")
        if "ec2" in checks:
            try:
                ec2=session.client("ec2"); resp=ec2.describe_instances()
                instances=[]
                for r in resp.get("Reservations",[]):
                    for inst in r.get("Instances",[]):
                        instances.append({"id":inst.get("InstanceId"),"type":inst.get("InstanceType"),"state":inst.get("State",{}).get("Name"),"public_ip":inst.get("PublicIpAddress"),"private_ip":inst.get("PrivateIpAddress")})
                results["ec2_instances"]=instances
                if instances:
                    findings.append(self.make_finding(title=f"EC2: {len(instances)} instances",target="aws:ec2",severity=Severity.INFO,description="EC2 instances enumerated.",evidence={"instances":instances[:5]},tags=["aws","ec2"]))
            except Exception as exc: self.log.warning(f"EC2 enum error: {exc}")
        if output_file:
            with open(output_file,"w") as fh: json.dump(results,fh,indent=2,default=str)
        return ModuleResult(success=True,output=results,findings=findings)
