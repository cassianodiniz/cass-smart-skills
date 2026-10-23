import { spawnSync } from 'node:child_process';
import { hyperframesCli } from '../../../scripts/runtime_paths.mjs';
try {
  const result=spawnSync(process.execPath,[hyperframesCli(),...process.argv.slice(2)],{stdio:'inherit',shell:false});
  if(result.error)throw result.error;
  process.exit(result.status??2);
}catch(e){console.error(e.message);process.exit(2);}
