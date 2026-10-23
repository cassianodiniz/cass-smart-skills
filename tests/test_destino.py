import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import smart_config

class PersistentTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name).resolve()
        self.env={'CASS_SMART_HOME':str(self.root/'settings')}
        self.patch=patch.dict(os.environ,self.env);self.patch.start();self.addCleanup(self.patch.stop)
        self.data=smart_config.proposta(self.root/'midia')
    def run_script(self,*args,script=None):
        return subprocess.run([sys.executable,str(script or ROOT/'skills/search/scripts/destino_pesquisa.py'),*args],cwd=self.root,capture_output=True,text=True)
    def test_no_configuration_no_files_created(self):
        r=self.run_script('tema');self.assertEqual(r.returncode,2)
        self.assertFalse((self.root/'midia').exists());self.assertFalse((ROOT/'skills/search/pesquisas').exists())
    def test_proposal_does_not_create_folders(self):
        self.assertFalse((self.root/'midia').exists());self.assertFalse(smart_config.arquivo().exists())
    def test_malformed_sections_are_rejected_clearly(self):
        import copy
        for key in ['canva','video','pastas']:
            for bad in [None, [], 'texto']:
                d=copy.deepcopy(self.data);d[key]=bad
                with self.subTest(section=key,value=bad), self.assertRaises(ValueError):smart_config.validar(d)
    def test_legacy_config_cannot_be_saved_inside_plugin(self):
        spec=importlib.util.spec_from_file_location('video_config_test',ROOT/'skills/video-maker/scripts/configurar.py')
        mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
        plugin=self.root/'plugin';plugin.mkdir()
        dados=self.root/'input.json';dados.write_text(json.dumps({'versao':1,'sistema':'linux','origem':'pasta','entrega':'pasta',**self.data['video'],'pastas':self.data['pastas']['videos']}))
        with patch.object(smart_config,'PLUGIN',plugin), self.assertRaises(ValueError):mod.salvar(plugin,dados)
        self.assertFalse((plugin/'.video-maker.json').exists())
    def test_save_and_resume_outside_plugin_and_working_directory(self):
        smart_config.salvar(self.data)
        target=Path(self.run_script('Nutrição / revisão','--data','2026-10-23').stdout.strip())
        self.assertEqual(target,self.root/'midia/pesquisas/nutricao-revisao-2026-10-23')
        self.assertTrue((target/'referencias').is_dir())
        self.assertEqual(smart_config.video_config()['pastas']['entrada'],str(self.root/'midia/videos/brutos'))
    def test_repeated_research_preserves_files(self):
        smart_config.salvar(self.data)
        first=Path(self.run_script('tema').stdout.strip());(first/'estudo.md').write_text('anterior')
        second=Path(self.run_script('tema').stdout.strip())
        self.assertNotEqual(first,second);self.assertEqual((first/'estudo.md').read_text(),'anterior')
    def test_invalid_date_does_not_escape(self):
        smart_config.salvar(self.data);r=self.run_script('tema','--data','../../outside')
        self.assertEqual(r.returncode,2);self.assertFalse((self.root/'outside').exists())
    def test_reject_internal_and_symlink_paths(self):
        link=self.root/'link';link.symlink_to(ROOT,target_is_directory=True)
        for path in [ROOT/'media',link/'media',Path.home()/'.codex/plugins/media']:
            with self.subTest(path=path),self.assertRaises(ValueError):smart_config.proposta(path)
    def test_bad_config_not_silently_replaced(self):
        smart_config.arquivo().parent.mkdir(parents=True);smart_config.arquivo().write_text('{invalid')
        self.assertEqual(self.run_script('tema').returncode,2)
        self.assertEqual(smart_config.arquivo().read_text(),'{invalid')
    def test_reconfiguration_keeps_backup_and_media(self):
        smart_config.salvar(self.data);clip=self.root/'midia/videos/brutos/clip.mp4';clip.write_bytes(b'original')
        d=smart_config.proposta(self.root/'outro');smart_config.salvar(d)
        self.assertEqual(clip.read_bytes(),b'original');self.assertEqual(len(list((self.root/'settings').glob('config-anterior-*.json'))),1)
        self.assertTrue((self.root/'settings/instaladores/instalar_video.py').exists())
    def test_template_is_persistent_and_invalid_type_rejected(self):
        self.data['canva']['template_padrao_id']='DA_TEST';smart_config.salvar(self.data)
        self.assertEqual(smart_config.carregar()['canva']['template_padrao_id'],'DA_TEST')
        self.data['canva']['template_padrao_id']=55
        with self.assertRaises(ValueError):smart_config.salvar(self.data)
    def test_unchanged_config_refreshes_installers_without_reset(self):
        smart_config.salvar(self.data)
        config_before=smart_config.arquivo().read_bytes()
        installer=Path(self.data['instaladores'])/'instalar_motion.mjs'
        installer.unlink()
        smart_config.salvar(self.data)
        self.assertTrue(installer.exists())
        self.assertEqual(smart_config.arquivo().read_bytes(),config_before)
        self.assertEqual(list((self.root/'settings').glob('config-anterior-*')),[])
    def test_upgrade_uses_same_external_data(self):
        smart_config.salvar(self.data)
        marker=self.root/'midia/videos/transcricoes/aula.json';marker.write_text('transcrição')
        for release in ['v1','v2']:
            pkg=self.root/release;(pkg/'scripts').mkdir(parents=True)
            shutil.copy2(ROOT/'scripts/smart_config.py',pkg/'scripts/smart_config.py')
            script=pkg/'skills/search/scripts/destino_pesquisa.py';script.parent.mkdir(parents=True)
            shutil.copy2(ROOT/'skills/search/scripts/destino_pesquisa.py',script)
            result=self.run_script('--conferir',script=script)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn(str(self.root/'midia/pesquisas'),result.stdout)
        shutil.rmtree(self.root/'v1')
        self.assertEqual(marker.read_text(),'transcrição')
        self.assertEqual(smart_config.carregar(),self.data)
    def test_legacy_video_config_has_precedence(self):
        smart_config.salvar(self.data)
        project=self.root/'project';project.mkdir()
        legacy=smart_config.video_config();legacy['pastas']={k:k for k in legacy['pastas']}
        (project/'.video-maker.json').write_text(json.dumps(legacy))
        r=subprocess.run([sys.executable,str(ROOT/'skills/video-maker/scripts/configurar.py'),'carregar','--projeto',str(project)],capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertEqual(json.loads(r.stdout)['pastas']['entrada'],str(project/'entrada'))
    def test_installer_rejects_plugin_destination_before_install(self):
        r=subprocess.run([sys.executable,str(ROOT/'skills/video-maker/scripts/instalar_ferramentas.py'),'--destino',str(ROOT/'tools')],capture_output=True,text=True)
        self.assertEqual(r.returncode,2);self.assertIn('fora da pasta do plugin',r.stderr);self.assertFalse((ROOT/'tools').exists())

if __name__=='__main__':unittest.main()
