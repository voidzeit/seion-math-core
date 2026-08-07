param(
    [ValidateSet('selftest','bilinear','hybrid','geometry')]
    [string]$Mode = 'hybrid',
    [int]$Seed = 42,
    [string]$RepoRoot = 'C:\Documents\0017\seion-training'
)

$ErrorActionPreference = 'Stop'
Set-Location $RepoRoot

$Python = '.\.venv\Scripts\python.exe'
$Trainer = '.\seion_train_v25.py'
$Train = '.\data\FB15K-237\train.txt'
$Valid = '.\data\FB15K-237\valid.txt'
$Test = '.\data\FB15K-237\test.txt'
$Kernel = '.\E8_Exact_v18_2\f_E8.npy'

if ($Mode -eq 'selftest') {
    & $Python $Trainer --self_test
    exit $LASTEXITCODE
}

$Common = @(
    '--train', $Train,
    '--valid', $Valid,
    '--test', $Test,
    '--D', '248',
    '--epochs', '48',
    '--batch_size', '2048',
    '--neg_k', '256',
    '--neg_mode', 'baseline',
    '--loss_mode', 'logistic',
    '--adversarial_temperature', '2.0',
    '--lr', '0.001',
    '--weight_decay', '0.00001',
    '--warmup_fraction', '0.05',
    '--grad_clip', '1.0',
    '--eval_batch', '1024',
    '--entity_block_eval', '4096',
    '--eval_every', '1',
    '--eval_amp',
    '--blackwell_tuned',
    '--amp',
    '--amp_dtype', 'bf16',
    '--allow_tf32',
    '--seed', "$Seed",
    '--early_stop_patience', '8'
)

switch ($Mode) {
    'bilinear' {
        $Out = ".\runs\V25_FB237_BILINEAR_SEED$Seed"
        $Args = @('--architecture','bilinear','--out_dir',$Out) + $Common
    }
    'hybrid' {
        $Out = ".\runs\V25_FB237_HYBRID_CP512_SEED$Seed"
        $Args = @(
            '--architecture','hybrid',
            '--f_path',$Kernel,
            '--cp_rank','512',
            '--cp_norm','layernorm',
            '--cp_residual_init','0.10',
            '--gate_per_relation',
            '--gate_init','fixed=0.15,cp=0.15,bilinear=0.70',
            '--distill_weight','0.02',
            '--distill_warmup_epochs','5',
            '--out_dir',$Out
        ) + $Common
    }
    'geometry' {
        $Out = ".\runs\V25_FB237_GEOMETRY_CP512_SEED$Seed"
        $Args = @(
            '--architecture','hybrid',
            '--f_path',$Kernel,
            '--cp_rank','512',
            '--cp_norm','layernorm',
            '--cp_residual_init','0.10',
            '--gate_per_relation',
            '--gate_init','fixed=0.15,cp=0.15,bilinear=0.70',
            '--distill_weight','0.02',
            '--distill_warmup_epochs','5',
            '--proj_rank','64',
            '--closure_weight','0.0001',
            '--closure_samples','16',
            '--fi_weight','0.0001',
            '--fi_samples','16',
            '--assoc_weight','0.0001',
            '--assoc_samples','16',
            '--audit_regularizer_grads',
            '--out_dir',$Out
        ) + $Common
    }
}

Write-Host "Running SEION v25 mode=$Mode seed=$Seed out=$Out"
& $Python $Trainer @Args
exit $LASTEXITCODE
