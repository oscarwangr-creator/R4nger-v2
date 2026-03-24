"""RTF v2.0 Test Suite"""
from __future__ import annotations
import asyncio, json, os, sys, tempfile, unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

class TestConfig(unittest.TestCase):
    def setUp(self):
        from framework.core.config import Config
        Config._instance = None
    def test_defaults_loaded(self):
        from framework.core.config import config
        config.load()
        self.assertIsNotNone(config.get("base_dir"))
        self.assertIsNotNone(config.get("api_port"))
    def test_set_and_get(self):
        from framework.core.config import config
        config.load()
        config.set("test_key","test_value")
        self.assertEqual(config.get("test_key"),"test_value")
    def test_env_override(self):
        os.environ["RTF_API_PORT"]="9999"
        from framework.core.config import Config; Config._instance=None
        from framework.core.config import config; config.load()
        self.assertEqual(config.get("api_port"),9999)
        del os.environ["RTF_API_PORT"]

class TestDatabase(unittest.TestCase):
    def setUp(self):
        from framework.db.database import Database; Database._instance=None
        self.tmp=tempfile.NamedTemporaryFile(suffix=".db",delete=False); self.tmp.close()
        from framework.db.database import db; db.init(self.tmp.name); self.db=db
    def tearDown(self): os.unlink(self.tmp.name)
    def test_job_lifecycle(self):
        import uuid
        self.db.create_job(f"j1-{uuid.uuid4()}","test","recon/test",{})
        job_id = self.db.list_jobs(limit=1)[0]["id"]
        self.db.start_job(job_id); j=self.db.get_job(job_id)
        self.assertEqual(j["status"],"running")
        self.db.finish_job(job_id,{"output":"done"})
        j=self.db.get_job(job_id); self.assertEqual(j["status"],"completed")
    def test_add_and_list_findings(self):
        import uuid
        job_id = f"j2-{uuid.uuid4()}"
        self.db.create_job(job_id,"find_job","recon/test",{})
        self.db.add_finding(job_id,"example.com","Test Finding",severity="high")
        findings=self.db.list_findings(job_id=job_id)
        self.assertEqual(len(findings),1); self.assertEqual(findings[0]["severity"],"high")
    def test_targets(self):
        self.db.add_target("example.com","domain")
        targets=self.db.list_targets()
        self.assertIn("example.com",[t["value"] for t in targets])

class TestBaseModule(unittest.TestCase):
    def _make_module(self):
        from framework.modules.base import BaseModule, ModuleResult
        class DummyModule(BaseModule):
            def info(self): return {"name":"dummy","description":"Test","category":"recon"}
            def _declare_options(self):
                self._register_option("target","Test target",required=True)
                self._register_option("count","A count",required=False,default=5,type=int)
            async def run(self) -> ModuleResult:
                return ModuleResult(success=True,output={"target":self.get("target"),"count":self.get("count")})
        return DummyModule()
    def test_defaults(self):
        mod=self._make_module(); self.assertEqual(mod.get("count"),5)
    def test_set_option(self):
        mod=self._make_module(); mod.set("target","example.com"); self.assertEqual(mod.get("target"),"example.com")
    def test_validate_raises_missing(self):
        from framework.core.exceptions import OptionValidationError
        mod=self._make_module()
        with self.assertRaises(OptionValidationError): mod.validate()
    def test_execute_success(self):
        mod=self._make_module()
        result=asyncio.run(mod.execute({"target":"test.com","count":"3"}))
        self.assertTrue(result.success); self.assertEqual(result.output["count"],3)

class TestModuleLoader(unittest.TestCase):
    def setUp(self):
        from framework.modules.loader import ModuleLoader; self.loader=ModuleLoader()
    def test_load_all_returns_count(self):
        count=self.loader.load_all(); self.assertGreater(count,0)
    def test_list_modules_not_empty(self):
        self.loader.load_all(); modules=self.loader.list_modules(); self.assertGreater(len(modules),0)
    def test_get_known_module(self):
        self.loader.load_all(); cls=self.loader.get("recon/subdomain_enum"); self.assertIsNotNone(cls)
    def test_search(self):
        self.loader.load_all(); results=self.loader.search("subdomain"); self.assertGreater(len(results),0)

class TestToolRegistry(unittest.TestCase):
    def setUp(self):
        from framework.registry.tool_registry import ToolRegistry; self.registry=ToolRegistry()
    def test_catalogue_loaded(self): self.assertGreater(len(self.registry.list_all()),0)
    def test_known_tool(self): entry=self.registry.get("nmap"); self.assertIsNotNone(entry)
    def test_summary(self):
        s=self.registry.summary(); self.assertIn("total_tools",s); self.assertIn("installed",s)

class TestWorkflowEngine(unittest.IsolatedAsyncioTestCase):
    def _make_wf(self, succeed=True):
        from framework.workflows.engine import Workflow, Step
        from framework.modules.base import BaseModule, ModuleResult
        class MockModule(BaseModule):
            _succeed=succeed
            def info(self): return {"name":"mock","description":"","category":"recon"}
            def _declare_options(self): self._register_option("target","T",required=False,default="test")
            async def run(self) -> ModuleResult:
                if not MockModule._succeed: return ModuleResult(success=False,error="Mock failure")
                return ModuleResult(success=True,output={"done":True})
        class TestWF(Workflow):
            name="test_wf"; description="Test"
            def steps(self): return [Step("step1",MockModule,required=False),Step("step2",MockModule,required=False)]
        return TestWF()
    async def test_successful_workflow(self):
        wf=self._make_wf(True); result=await wf.run({"target":"example.com"})
        self.assertTrue(result.success); self.assertEqual(len(result.steps),2)
    async def test_workflow_to_dict(self):
        wf=self._make_wf(); result=await wf.run(); d=result.to_dict()
        self.assertIn("workflow",d); self.assertIn("steps",d)
    async def test_builtin_workflows(self):
        from framework.workflows.engine import BUILTIN_WORKFLOWS
        self.assertIn("full_recon",BUILTIN_WORKFLOWS)
        self.assertIn("identity_fusion",BUILTIN_WORKFLOWS)
        self.assertIn("full_ad_compromise",BUILTIN_WORKFLOWS)
    async def test_workflow_builder(self):
        from framework.workflows.engine import WorkflowBuilder
        from framework.modules.base import BaseModule, ModuleResult
        class B(BaseModule):
            def info(self): return {"name":"b","description":"","category":"recon"}
            def _declare_options(self): pass
            async def run(self) -> ModuleResult: return ModuleResult(success=True)
        wf=(WorkflowBuilder("custom").with_options(target="example.com").add_step("step1",B).build())
        result=await wf.run(); self.assertTrue(result.success)

class TestScheduler(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        from framework.scheduler.scheduler import Scheduler; self.scheduler=Scheduler(max_workers=2); await self.scheduler.start()
    async def asyncTearDown(self): await self.scheduler.stop()
    async def test_submit_and_complete(self):
        async def noop(): return "done"
        job=self.scheduler.submit("test",noop); completed=await self.scheduler.wait_for(job.id,poll_interval=0.1)
        self.assertEqual(completed.result,"done")
    async def test_stats(self):
        stats=self.scheduler.stats(); self.assertIn("total",stats)

if __name__ == "__main__":
    unittest.main(verbosity=2)

class TestAutonomousExtensions(unittest.IsolatedAsyncioTestCase):
    async def test_extreme_workflows_registered(self):
        from framework.workflows.engine import BUILTIN_WORKFLOWS
        self.assertIn("identity_fusion_extreme", BUILTIN_WORKFLOWS)
        self.assertIn("attack_surface_mapping", BUILTIN_WORKFLOWS)
        self.assertIn("external_pentest_full", BUILTIN_WORKFLOWS)
        self.assertIn("threat_intelligence_pipeline", BUILTIN_WORKFLOWS)

    async def test_identity_fusion_extreme_module(self):
        from framework.modules.osint.identity_fusion_extreme import IdentityFusionExtremeModule
        result = await IdentityFusionExtremeModule().execute({"username": "alice.ops", "email": "alice@example.com", "domain": "example.com"})
        self.assertTrue(result.success)
        self.assertIn("graph", result.output)
        self.assertGreaterEqual(result.output["risk_score"], 0.2)

    async def test_pipeline_engine_v2(self):
        from framework.automation.pipeline_v2 import PipelineEngineV2, PipelineStepV2
        pipeline = PipelineEngineV2()
        async def step1(ctx): return {"alpha": 1}
        async def step2(ctx): return {"beta": ctx["alpha"] + 1}
        pipeline.add_step(PipelineStepV2("a", step1)).add_step(PipelineStepV2("b", step2, condition=lambda ctx: "alpha" in ctx))
        result = await pipeline.run()
        self.assertTrue(result.success)
        self.assertEqual(result.context["beta"], 2)

    async def test_autonomous_agent_runs(self):
        from framework.ai.autonomous_agent import AutonomousAgent
        agent = AutonomousAgent()
        result = await agent.run({"seed": {"username": "alice.ops", "email": "alice@example.com", "domain": "example.com"}, "primary_goal": "Map identity"}, max_iterations=1)
        self.assertIn("execution_log", result)
        self.assertTrue(result["execution_log"])


class TestMegaIntegrationModules(unittest.IsolatedAsyncioTestCase):
    async def test_nexus_identity_pipeline_module(self):
        from framework.modules.osint.nexus_identity_pipeline import NexusIdentityPipelineModule
        result = await NexusIdentityPipelineModule().execute({"username": "alice.ops", "email": "alice@example.com", "phone": "(555) 123-4567", "company": "Example Corp"})
        self.assertTrue(result.success)
        self.assertEqual(result.output["schema_version"], "rtf-intel/1.0")
        self.assertIn("neo4j", result.output["integrations"])

    async def test_casm_pipeline_module(self):
        from framework.modules.recon.casm_pipeline import CASMPipelineModule
        result = await CASMPipelineModule().execute({"target": "example.com"})
        self.assertTrue(result.success)
        self.assertEqual(result.output["module"], "recon/casm_pipeline")

    async def test_credential_intelligence_module(self):
        from framework.modules.post_exploitation.credential_intelligence import CredentialIntelligenceModule
        result = await CredentialIntelligenceModule().execute({"full_name": "Alice Example", "company": "ExampleCorp", "city": "Austin", "pet_name": "Pixel", "birth_year": "1992"})
        self.assertTrue(result.success)
        self.assertGreaterEqual(len(result.output["entities"]["password_candidates"]), 5)

    async def test_physical_wireless_audit_module(self):
        from framework.modules.wireless.physical_wireless_audit import PhysicalWirelessAuditModule
        result = await PhysicalWirelessAuditModule().execute({"target": "HQ badge readers"})
        self.assertTrue(result.success)
        self.assertEqual(result.output["module"], "wireless/physical_wireless_audit")


class TestV4UpgradePipeline(unittest.TestCase):
    def test_upgrade_pipeline_builds_architecture(self):
        from framework.upgrade import UpgradePipeline
        report = UpgradePipeline(repo_root=Path(__file__).resolve().parents[2]).run()
        self.assertEqual(report["version"], "4.0.0")
        self.assertEqual(len(report["agents"]), 7)
        self.assertIn("module_system", report["architecture"])

    def test_upgrade_report_artifacts_written(self):
        from framework.upgrade import build_v4_upgrade_report
        report = build_v4_upgrade_report(Path(__file__).resolve().parents[2])
        self.assertTrue(Path(report["artifacts"]["json"]).name.endswith("V4_UPGRADE_REPORT.json"))
        self.assertTrue(Path(report["artifacts"]["markdown"]).name.endswith("V4_ARCHITECTURE_REPORT.md"))

    def test_cli_parser_has_upgrade_command(self):
        import rtf as rtf_cli
        parser = rtf_cli.build_parser()
        args = parser.parse_args(["upgrade", "analyze"])
        self.assertEqual(args.command, "upgrade")
        self.assertEqual(args.upgrade_subcommand, "analyze")


class TestArchitectureEngines(unittest.IsolatedAsyncioTestCase):
    async def test_engine_registry_contains_requested_services(self):
        from framework.engines import engine_registry
        names = {spec.name for spec in engine_registry.list()}
        self.assertIn("rtf-core", names)
        self.assertIn("rtf-breach-engine", names)
        self.assertIn("rtf-report-engine", names)
        self.assertEqual(len(names), 12)

    async def test_architecture_module_executes(self):
        from framework.modules.architecture.rtf_breach_engine import RtfBreachEngineModule
        result = await RtfBreachEngineModule().execute({"target": "example.com", "operation_id": "op-1"})
        self.assertTrue(result.success)
        self.assertEqual(result.output["name"], "rtf-breach-engine")
        self.assertEqual(result.output["async_pipeline"]["queue"], "queue:breach")

    async def test_engine_mesh_workflow_registered(self):
        from framework.workflows.engine import BUILTIN_WORKFLOWS
        self.assertIn("engine_mesh", BUILTIN_WORKFLOWS)


class TestArchitectureCli(unittest.TestCase):
    def test_cli_parser_has_engine_command(self):
        import rtf as rtf_cli
        parser = rtf_cli.build_parser()
        args = parser.parse_args(["engine", "info", "rtf-core"])
        self.assertEqual(args.command, "engine")
        self.assertEqual(args.engine_subcommand, "info")
        self.assertEqual(args.name, "rtf-core")
