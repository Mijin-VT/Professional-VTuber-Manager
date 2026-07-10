[Setup]
AppName=VTuber Manager
AppVersion=1.0
DefaultDirName={autopf}\VTuber Manager
DefaultGroupName=VTuber Manager
OutputBaseFilename=VTManager_Setup
OutputDir=D:\Desktop\AGENTES\vtmanager_BASE\VTuber-Manager_subir
SetupIconFile=icons\vtmanager.ico
Compression=lzma
SolidCompression=yes
DisableProgramGroupPage=yes
DisableWelcomePage=no
PrivilegesRequired=admin

[Files]
Source: "main.py"; DestDir: "{app}"
Source: "debug_run.py"; DestDir: "{app}"
Source: "requirements.txt"; DestDir: "{app}"
Source: "INSTALL.bat"; DestDir: "{app}"
Source: "vtmanager.bat"; DestDir: "{app}"
Source: "vtmanager.vbs"; DestDir: "{app}"
Source: "ruvector.db"; DestDir: "{app}"
Source: "app\*"; DestDir: "{app}\app"; Flags: recursesubdirs createallsubdirs skipifsourcedoesntexist
Source: "bin\*"; DestDir: "{app}\bin"; Flags: recursesubdirs createallsubdirs skipifsourcedoesntexist
Source: "config\*"; DestDir: "{app}\config"; Flags: recursesubdirs createallsubdirs skipifsourcedoesntexist
Source: "data\*"; DestDir: "{app}\data"; Flags: recursesubdirs createallsubdirs skipifsourcedoesntexist
Source: "icons\*"; DestDir: "{app}\icons"; Flags: recursesubdirs createallsubdirs skipifsourcedoesntexist
Source: "models\*"; DestDir: "{app}\models"; Flags: recursesubdirs createallsubdirs skipifsourcedoesntexist
Source: "plugins\*"; DestDir: "{app}\plugins"; Flags: recursesubdirs createallsubdirs skipifsourcedoesntexist
Source: "programs\*"; DestDir: "{app}\programs"; Flags: recursesubdirs createallsubdirs skipifsourcedoesntexist


[Icons]
Name: "{group}\VTuber Manager"; Filename: "{app}\vtmanager.vbs"; IconFilename: "{app}\icons\vtmanager.ico"
Name: "{autodesktop}\VTuber Manager"; Filename: "{app}\vtmanager.vbs"; IconFilename: "{app}\icons\vtmanager.ico"

[Run]
Filename: "{app}\vtmanager.vbs"; Description: "Launch VTuber Manager"; Flags: shellexec postinstall skipifsilent

[Code]
type
  TMsg = record
    hwnd: HWND;
    message: Cardinal;
    wParam: Longint;
    lParam: Longint;
    time: DWORD;
    pt: TPoint;
  end;

function PeekMessage(var lpMsg: TMsg; hWnd: HWND; wMsgFilterMin, wMsgFilterMax, wRemoveMsg: Cardinal): Boolean;
  external 'PeekMessageW@user32.dll stdcall';

function TranslateMessage(const lpMsg: TMsg): Boolean;
  external 'TranslateMessage@user32.dll stdcall';

function DispatchMessage(const lpMsg: TMsg): Longint;
  external 'DispatchMessageW@user32.dll stdcall';

procedure ProcessMessages();
var
  Msg: TMsg;
begin
  while PeekMessage(Msg, 0, 0, 0, 1) do begin
    TranslateMessage(Msg);
    DispatchMessage(Msg);
  end;
end;

var
  PythonProgressGauge: TNewProgressBar;
  PythonStatusLabel: TNewStaticText;

procedure InitializeWizard();
begin
  { Create the new label and progress bar on wpInstalling page }
  PythonStatusLabel := TNewStaticText.Create(WizardForm);
  PythonStatusLabel.Parent := WizardForm.InstallingPage;
  PythonStatusLabel.Left := WizardForm.StatusLabel.Left;
  PythonStatusLabel.Top := WizardForm.ProgressGauge.Top + WizardForm.ProgressGauge.Height + ScaleY(12);
  PythonStatusLabel.Width := WizardForm.StatusLabel.Width;
  PythonStatusLabel.Height := WizardForm.StatusLabel.Height;
  PythonStatusLabel.Font.Name := WizardForm.StatusLabel.Font.Name;
  PythonStatusLabel.Font.Size := WizardForm.StatusLabel.Font.Size;
  PythonStatusLabel.Font.Color := WizardForm.StatusLabel.Font.Color;
  PythonStatusLabel.Font.Style := WizardForm.StatusLabel.Font.Style;
  PythonStatusLabel.Caption := 'Preparando la instalación de dependencias...';
  PythonStatusLabel.Visible := False;

  PythonProgressGauge := TNewProgressBar.Create(WizardForm);
  PythonProgressGauge.Parent := WizardForm.InstallingPage;
  PythonProgressGauge.Left := WizardForm.ProgressGauge.Left;
  PythonProgressGauge.Top := PythonStatusLabel.Top + PythonStatusLabel.Height + ScaleY(4);
  PythonProgressGauge.Width := WizardForm.ProgressGauge.Width;
  PythonProgressGauge.Height := WizardForm.ProgressGauge.Height;
  PythonProgressGauge.Min := 0;
  PythonProgressGauge.Max := 100;
  PythonProgressGauge.Position := 0;
  PythonProgressGauge.Visible := False;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ProgressFile: String;
  StatusFile: String;
  Command: String;
  ResultCode: Integer;
  ProgressStr: AnsiString;
  ProgressVal: Integer;
  StatusStr: AnsiString;
  PythonInstaller: String;
  LFSInstaller: String;
  PSCommand: String;
begin
  if CurStep = ssPostInstall then begin
    { Show the second progress bar and status }
    PythonStatusLabel.Visible := True;
    PythonProgressGauge.Visible := True;
    PythonProgressGauge.Position := 0;

    { 1. Download and Install Python }
    PythonInstaller := ExpandConstant('{tmp}\python-3.12.0-amd64.exe');
    DeleteFile(PythonInstaller);
    
    PythonStatusLabel.Caption := 'Descargando instalador de Python...';
    PSCommand := '-Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri ''https://www.python.org/ftp/python/3.12.0/python-3.12.0-amd64.exe'' -OutFile ''' + PythonInstaller + '''"';
    
    { Run powershell hidden and wait until download completes }
    if Exec('powershell.exe', PSCommand, ExpandConstant('{tmp}'), SW_HIDE, ewWaitUntilTerminated, ResultCode) then begin
      if FileExists(PythonInstaller) then begin
        PythonStatusLabel.Caption := 'Ejecutando instalador de Python (acepte advertencias)...';
        { Unblock using powershell just in case }
        Exec('powershell.exe', '-Command "Unblock-File -Path ''' + PythonInstaller + '''"', ExpandConstant('{tmp}'), SW_HIDE, ewWaitUntilTerminated, ResultCode);
        { Run in the foreground and wait }
        Exec(PythonInstaller, '', ExpandConstant('{tmp}'), SW_SHOWNORMAL, ewWaitUntilTerminated, ResultCode);
        DeleteFile(PythonInstaller);
      end else begin
        MsgBox('No se pudo descargar el instalador de Python.', mbError, MB_OK);
      end;
    end else begin
      MsgBox('No se pudo iniciar la descarga de Python.', mbError, MB_OK);
    end;

    { 2. Download and Install Git LFS }
    LFSInstaller := ExpandConstant('{tmp}\git-lfs-installer.exe');
    DeleteFile(LFSInstaller);
    
    PythonStatusLabel.Caption := 'Descargando instalador de Git LFS...';
    PSCommand := '-Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri ''https://github.com/git-lfs/git-lfs/releases/download/v3.6.0/git-lfs-windows-v3.6.0.exe'' -OutFile ''' + LFSInstaller + '''"';
    
    { Run powershell hidden and wait until download completes }
    if Exec('powershell.exe', PSCommand, ExpandConstant('{tmp}'), SW_HIDE, ewWaitUntilTerminated, ResultCode) then begin
      if FileExists(LFSInstaller) then begin
        PythonStatusLabel.Caption := 'Ejecutando instalador de Git LFS (acepte advertencias)...';
        { Unblock using powershell just in case }
        Exec('powershell.exe', '-Command "Unblock-File -Path ''' + LFSInstaller + '''"', ExpandConstant('{tmp}'), SW_HIDE, ewWaitUntilTerminated, ResultCode);
        { Run in the foreground and wait }
        Exec(LFSInstaller, '', ExpandConstant('{tmp}'), SW_SHOWNORMAL, ewWaitUntilTerminated, ResultCode);
        DeleteFile(LFSInstaller);
      end else begin
        MsgBox('No se pudo descargar el instalador de Git LFS.', mbError, MB_OK);
      end;
    end else begin
      MsgBox('No se pudo iniciar la descarga de Git LFS.', mbError, MB_OK);
    end;

    PythonStatusLabel.Caption := 'Instalando dependencias de Python en segundo plano...';
    
    ProgressFile := ExpandConstant('{tmp}\install_progress.txt');
    StatusFile := ExpandConstant('{tmp}\install_status.txt');
    
    { Delete any stale status/progress files }
    DeleteFile(ProgressFile);
    DeleteFile(StatusFile);

    { Prepare the silent background execution of INSTALL.bat }
    Command := '/c ""' + ExpandConstant('{app}\INSTALL.bat') + '"" ""' + ProgressFile + '"" > ""' + ExpandConstant('{app}\install_log.txt') + '"" 2>&1 && echo SUCCESS > ""' + StatusFile + '"" || echo FAILED > ""' + StatusFile + '""';
    
    { Run hidden (SW_HIDE = 0) and do not wait natively so we can loop }
    if Exec('cmd.exe', Command, ExpandConstant('{app}'), SW_HIDE, ewNoWait, ResultCode) then begin
      { Loop until the status file exists }
      while not FileExists(StatusFile) do begin
        Sleep(250);
        { Process messages to keep UI responsive and redrawing }
        ProcessMessages;
        
        { Read progress if available }
        if FileExists(ProgressFile) then begin
          if LoadStringFromFile(ProgressFile, ProgressStr) then begin
            ProgressVal := StrToIntDef(Trim(ProgressStr), 0);
            if ProgressVal > 0 then begin
              PythonProgressGauge.Position := ProgressVal;
            end;
          end;
        end;
      end;
      
      { Installation finished, read status }
      if FileExists(StatusFile) then begin
        LoadStringFromFile(StatusFile, StatusStr);
        if Pos('SUCCESS', StatusStr) > 0 then begin
          PythonProgressGauge.Position := 100;
          PythonStatusLabel.Caption := 'Instalación de dependencias completada.';
          MsgBox('La instalación de VTuber Manager, Python y todas sus dependencias se completó exitosamente.', mbInformation, MB_OK);
        end else begin
          PythonStatusLabel.Caption := 'Fallo en la instalación de dependencias.';
          MsgBox('Ocurrió un problema durante la instalación de Python o sus dependencias. Por favor, ejecuta INSTALL.bat manualmente para resolverlo.', mbError, MB_OK);
        end;
      end else begin
        PythonStatusLabel.Caption := 'No se pudo verificar el estado.';
        MsgBox('No se pudo determinar el estado de la instalación de las dependencias.', mbError, MB_OK);
      end;
    end else begin
      PythonStatusLabel.Caption := 'No se pudo iniciar INSTALL.bat.';
      MsgBox('No se pudo iniciar el instalador de dependencias (INSTALL.bat).', mbError, MB_OK);
    end;
    
    { Cleanup temporary files }
    DeleteFile(ProgressFile);
    DeleteFile(StatusFile);
  end;
end;
