# Arquitetura e decisões

## Componentes

O Nginx entrega o React compilado e encaminha `/api` à aplicação FastAPI. O FastAPI valida as entradas com Pydantic e persiste os registros usando SQLAlchemy. PostgreSQL é o banco do Compose; SQLite atende desenvolvimento e os testes locais. Alembic controla o esquema.

O frontend usa JavaScript e JSX, sem TypeScript. A API é Python. O layout foi reaproveitado da primeira versão publicada, mas o backend e o acesso foram reimplementados, sem dependência do Cloudflare D1 ou do login ChatGPT.

## Regras importantes

- Dinheiro é inteiro em centavos, sem aritmética de ponto flutuante no backend.
- Preços da venda são consultados pelo backend; valores enviados pelo navegador não são aceitos no item da venda.
- Custos, preços, nomes e quantidades são preservados em cada venda, como fotografia daquele momento.
- Um identificador repetido com o mesmo conteúdo não duplica uma venda. O mesmo identificador com outro conteúdo retorna conflito.
- Em PostgreSQL, a criação da venda bloqueia as linhas dos produtos enquanto monta o registro. Alterações de situação usam bloqueio de linha para evitar transições concorrentes inválidas.
- Situações: `pending → paid → cancelled` ou `pending → cancelled`. Uma venda cancelada não volta para paga.
- Cancelamento no banco de dados não executa estorno financeiro.
- Relatórios da interface contam apenas vendas pagas. O CSV também permite auditar pendentes e canceladas. Total/taxa/custo da venda aparecem só na primeira linha para não duplicar a soma.
- O resultado é uma estimativa: receita menos custos cadastrados e taxas informadas em reais; outros gastos e impostos não estão incluídos.
- O catálogo de referência não grava produtos fictícios no banco. Itens sem preço podem ser editados, mas não vendidos.

## Sessão e tela do cliente

Há um operador configurado em variáveis de ambiente. O login compara a credencial em tempo constante e cria um token aleatório. Só o hash desse token é armazenado no banco. O navegador recebe cookie HttpOnly com SameSite Strict. Use Secure em HTTPS.

A tela do cliente precisa de sessão válida. Não é um catálogo público na internet. O endpoint de exibição retorna somente nome, categoria, preço e itens selecionados, sem custos ou dados do comprador. Há um estado compartilhado por instalação, pensado para um operador. Sem heartbeat, a compra sai da tela após 90 segundos e o catálogo reaparece.

## Endpoints

| Método | Caminho | Função |
|---|---|---|
| GET | `/api/health` | Saúde do servidor e banco |
| POST | `/api/login` | Iniciar sessão |
| GET | `/api/session` | Consultar sessão |
| POST | `/api/logout` | Encerrar sessão |
| GET | `/api/data` | Produtos e histórico do operador |
| POST | `/api/products` | Criar/editar produto |
| POST | `/api/sales` | Registrar venda com idempotência |
| PATCH | `/api/sales/{id}/status` | Confirmar ou cancelar registro |
| GET | `/api/sales/{id}/receipt` | Recibo textual de venda paga |
| POST | `/api/sales/{id}/email` | Enviar pelo Resend, se configurado |
| GET | `/api/display` | Catálogo e compra para o cliente |
| POST | `/api/display` | Atualizar a compra exibida |

Valores, objetos e exemplos interativos estão disponíveis no OpenAPI (`/docs`). As rotas protegidas exigem login por cookie; para chamadas de escrita, use `X-CSRF-Protection: 1`.

## Próximas evoluções

1. Backup e restauração do banco com procedimento ensaiado.
2. Vários eventos, operadores e caixas independentes.
3. Validação de voucher na recepção, uso único e QR Code.
4. Estoque com movimentações e inventário.
5. Provedor de SMS, com telefone do comprador e link de acesso restrito ao recibo.
6. Observabilidade e deploy de imagens pelo GitHub Actions.
7. Terraform para infraestrutura escolhida após estimativa de custo.

O desenho atual com Nginx, FastAPI e PostgreSQL pode rodar em uma VM. Adotar Lambda e DynamoDB é outra etapa de adaptação; trocar a infraestrutura não troca o modelo de persistência automaticamente.
