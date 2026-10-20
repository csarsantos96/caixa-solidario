# Bilhete Solidário

Sistema de caixa para venda de alimentos e emissão de vouchers em eventos. Criado a partir do fluxo do seminário **Varejo que dá resultado**, do SEBRAE.

**Python + FastAPI · React + JavaScript · Vite · Tailwind CSS · PostgreSQL · Docker Compose**

## Iniciar com Docker

Pré-requisitos: Docker Engine com Docker Compose v2 e Python 3 para gerar a configuração.

Na pasta do projeto:

```bash
python3 scripts/configure.py
docker compose up --build -d
```

Acesse **http://localhost:8080**. Usuário: `admin`. A senha é gerada e exibida pelo primeiro comando; ela também fica no arquivo local `.env`.

O script não sobrescreve um `.env` existente. Guarde a senha. O `.env` já está ignorado pelo Git e não vem neste pacote.

O Compose inicia PostgreSQL, aplica as migrações Alembic, sobe a API e serve o frontend pelo Nginx. O banco tem volume persistente e não expõe sua porta à rede. A primeira inicialização exige internet para baixar imagens e dependências.

```bash
docker compose ps
docker compose logs -f backend
docker compose down
```

`docker compose down` preserva o banco. Não use `down -v` se quiser manter seus dados.

## Usar no evento

1. Abra **Produtos → Editar** e informe custo e preço. O catálogo contém 17 itens e variações, inicialmente sem preços.
2. Abra **Caixa** e use **Adicionar à compra**.
3. Abra **Tela do cliente**, mova a janela ao monitor externo e use F11. A área de trabalho deve estar em modo estendido, sem espelhamento.
4. Receba por Pix, cartão, dinheiro ou link no serviço que você utiliza.
5. Só depois da aprovação, confirme o recebimento no sistema. Se ainda não recebeu, salve como pendente.
6. Em **Vendas → Ver venda**, baixe o recibo ou imprima o voucher/salve como PDF.
7. Use **Relatórios** para conferir receita, quantidades, custos e taxas informadas; baixe o CSV.

A tela do cliente mostra produtos ativos com preço quando a cesta está vazia. Ao adicionar itens, mostra a compra e o total. Atualiza a cada dois segundos e também recebe atualizações imediatas entre janelas do mesmo navegador. Para outro navegador, entre com o mesmo operador. Use **um caixa operador ativo** por instalação.

O voucher corresponde a **uma pessoa por venda paga**, com código ligado à venda. Reimpressões mantêm o código. Combine essa regra com a organização; a recepção recolhe o papel. Não há leitura de QR Code ou controle eletrônico de resgate nesta versão.

Pagamentos são confirmados pelo operador. O sistema não cobra cartões, não consulta o PagBank e não estorna valores quando um registro é cancelado. Recibos não têm valor fiscal.

## Envio de recibos

- **Baixar recibo** gera um arquivo de texto.
- **Abrir no e-mail** prepara destinatário, assunto e corpo no aplicativo configurado no computador. O operador clica em Enviar nesse aplicativo.
- **Imprimir voucher / salvar PDF** abre um documento para a impressão do navegador.
- **Envio automático** é opcional, usando Resend. Configure em `.env`:

```dotenv
RESEND_API_KEY=sua-chave
RECEIPT_FROM="Bilhete Solidário <recibo@bilhetesolidario.com.br>"
```

O remetente precisa estar verificado no provedor. Recrie o backend após alterar variáveis:

```bash
docker compose up -d --force-recreate backend
```

Com as duas configurações ativas, informe o e-mail do cliente ao fechar a compra. Ao confirmar o pagamento no caixa (ou marcar uma venda pendente como paga), a interface solicita o envio diretamente, sem abrir o aplicativo de e-mail. O recibo tem layout azul do Bilhete Solidário, itens e quantidades salvos na venda, preços unitários, total, forma de pagamento e voucher. Também inclui uma versão em texto para leitores de e-mail sem HTML.

Se o envio falhar, a venda permanece salva e o operador pode tentar novamente em **Vendas → Ver venda → Enviar recibo por e-mail**. Essa tentativa automática depende da interface aberta; não há fila de envio em segundo plano. O aceite pelo provedor não garante entrega na caixa de entrada. A implementação usa idempotência e registra o aceite. SMS e WhatsApp ainda não estão implementados.

## Rodar sem Docker

Requisitos: Python 3.12 e Node.js 24. Para testar localmente sem PostgreSQL, o backend também aceita SQLite.

Na raiz, gere a configuração:

```bash
python3 scripts/configure.py
```

No primeiro terminal:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
alembic upgrade head
uvicorn app.asgi:app --reload --host 127.0.0.1 --port 8000
```

A configuração gerada usa SQLite nesse modo. Para PostgreSQL, altere `DATABASE_URL` para `postgresql+psycopg://usuario:senha@host:5432/banco`.

No segundo terminal:

```bash
cd frontend
npm ci
npm run dev
```

Abra **http://localhost:5173**. O Vite encaminha `/api` ao backend na porta 8000. Na versão com Docker, a URL é **http://localhost:8080**. O acesso à documentação da API é `/docs` em qualquer um desses endereços.

## Testar e compilar

```bash
cd backend
pytest -q
alembic check
```

```bash
cd frontend
npm ci
npm run build
```

O CI em `.github/workflows/ci.yml` prepara PostgreSQL, aplica e verifica migrações, executa os testes do backend e compila o frontend. Ele **não publica em nuvem** e não precisa de credenciais AWS.

Testes locais executados na entrega: 15 testes de integração de API com SQLite, migração Alembic, verificação do esquema, build Vite e teste HTTP do frontend ao backend pelo proxy Vite. O SQL da migração também foi gerado para PostgreSQL. Docker, PostgreSQL real, CI remoto e interação visual em navegador não foram executados neste ambiente. O envio real de e-mails não foi acionado; o provedor foi simulado nos testes.

## Enviar ao GitHub

Crie um repositório vazio na sua conta. Depois execute na raiz deste projeto:

```bash
git init -b main
git add .
git status
git commit -m "feat: add event checkout with FastAPI and React"
git remote add origin https://github.com/SEU_USUARIO/caixa-solidario.git
git push -u origin main
```

Troque `SEU_USUARIO` pelo seu usuário. Se o repositório tiver outro nome, ajuste a URL. Antes do commit, confira `git status`: `.env`, bancos, backups e dependências não devem aparecer.

O pacote contém código e o catálogo inicial, sem senhas ou dados dos compradores. Os preços e o histórico da versão publicada anteriormente não foram copiados para este banco. A versão online continua disponível separadamente; esta entrega não migra automaticamente seus dados.

## Estrutura

```text
backend/
  app/             API, validação, banco, autenticação e recibos
  migrations/      versões do esquema Alembic
  tests/           testes de integração
frontend/
  src/             interface React e cliente da API
  nginx.conf       proxy da versão com Docker
scripts/
  configure.py     geração local de credenciais
docs/
  arquitetura.md   decisões e próximos passos
.github/workflows/
  ci.yml           testes e build no GitHub Actions
compose.yaml       aplicação completa
.env.example       nomes das configurações
```

## Acesso em rede e hospedagem

Por padrão, a aplicação escuta apenas em `127.0.0.1`. Para outro dispositivo na sua rede local, ajuste `BIND_ADDRESS=0.0.0.0` no `.env` e recrie o frontend. Use o IP do computador e a porta 8080 no segundo dispositivo. Mantenha a rede restrita durante o evento.

Para publicar na internet, configure domínio e HTTPS em um proxy reverso, defina `COOKIE_SECURE=true` e proteja o banco e os backups. O login é próprio desta aplicação, com sessão em cookie HttpOnly. O limitador de tentativas de login desta versão é local ao processo; use apenas um worker ou acrescente um limitador compartilhado ao escalar.

As chamadas de escrita exigem um cabeçalho próprio de proteção CSRF e a aplicação não habilita CORS entre origens. Frontend e API devem usar a mesma origem, como no Nginx e no Vite fornecidos. O caixa precisa de conexão com o servidor; não há fila offline.

A aplicação já pode ser containerizada em outra infraestrutura. Terraform e migração para serviços gerenciados AWS ficam para uma etapa posterior, depois de definir custo e arquitetura. Nenhum recurso AWS é criado pelo pacote.

Documentação das tecnologias: [FastAPI](https://fastapi.tiangolo.com/), [React](https://react.dev/), [Vite](https://vite.dev/), [SQLAlchemy](https://docs.sqlalchemy.org/), [Alembic](https://alembic.sqlalchemy.org/).

## Verificação de credenciais expostas

O workflow `.github/workflows/secrets.yml` usa o [Gitleaks](https://github.com/gitleaks/gitleaks) para procurar possíveis senhas, tokens, chaves privadas e credenciais no histórico Git disponível, em cada push, pull request e às segundas-feiras. Também pode ser executado manualmente em **Actions → Secret scan → Run workflow**.

A verificação falha quando encontra uma possível credencial e oculta os valores nos logs. Não exige configurar secrets do GitHub. Para impedir merges quando ela falhar, configure a regra de proteção da branch para exigir o check **Detect exposed credentials**.

Se uma credencial real for detectada, revogue ou troque a credencial no serviço de origem; apagar apenas o arquivo atual não remove o segredo do histórico. A detecção usa padrões e pode produzir falsos positivos ou deixar passar senhas: um resultado aprovado não garante ausência de credenciais.

## Quantidades e peso dos alimentos

Em **Produtos → Editar**, informe o **Peso por unidade (g)**: 500 para um pacote de 500 g, 1000 para 1 kg. Quando disponível, o formulário sugere o peso escrito no nome. O peso é opcional para produtos sem massa conhecida.

Em **Relatórios**, o resumo por alimento soma embalagens de tamanhos diferentes e o detalhe mostra unidades, peso por unidade, peso total em kg e receita. Exemplo: 3 pacotes de macarrão de 500 g e 2 de 1 kg = 5 unidades e 3,5 kg. Os totais usam apenas vendas pagas no período selecionado; a exportação CSV também inclui peso por unidade e peso total por item. Ao final do mesmo CSV, há resumos por alimento e por embalagem, com quantidade total, peso total conhecido em kg, unidades sem peso e receita das vendas pagas do período, além do total geral.

Novas vendas guardam o peso vigente na venda. Para vendas antigas sem esse campo, usa-se o peso explícito no nome salvo do item. Itens sem peso são sinalizados como não informados e não entram na soma em kg; volumes como ml e litros não são convertidos em massa. A atualização do Docker aplica automaticamente a migração que adiciona o campo ao cadastro.
