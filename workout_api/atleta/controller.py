from datetime import datetime
from uuid import uuid4
from fastapi import APIRouter, Body, HTTPException, status
from pydantic import UUID4
from sqlalchemy import select
from fastapi_pagination import LimitOffsetPage, add_pagination, paginate

from workout_api.atleta.models import AtletaModel
from workout_api.atleta.schemas import AtletaIn, AtletaOut, AtletaOutPersonalizado, AtletaUpdate
from workout_api.categorias.models import CategoriaModel
from workout_api.centro_treinamento.models import CentroTreinamentoModel
from workout_api.contrib.dependencies import DatabaseDependency

router = APIRouter()

@router.post(
    '/', 
    summary='Criar novo atleta', 
    status_code=status.HTTP_201_CREATED,
    response_model=AtletaOut
)
async def post(db_session: DatabaseDependency, atleta_in: AtletaIn = Body(...)):
    nome_categoria = atleta_in.categoria.nome
    nome_centro_treinamento = atleta_in.centro_treinamento.nome

    categoria = (await db_session.execute(select(CategoriaModel).filter_by(nome=nome_categoria))).scalars().first()

    if not categoria:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f'A categoria {nome_categoria} não foi encontrada')
    

    centro_treinamento = (await db_session.execute(select(CentroTreinamentoModel).filter_by(nome=nome_centro_treinamento))).scalars().first()

    if not centro_treinamento:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f'O centro de treinamento {nome_centro_treinamento} não foi encontrado')
        
    cpf_validado = (await db_session.execute(select(AtletaModel).filter_by(cpf=atleta_in.cpf))).scalars().first()

    if atleta_in.cpf == cpf_validado.cpf:
        raise HTTPException(status_code=status.HTTP_303_SEE_OTHER, detail=f'Já existe um atleta cadastrado com o cpf: {cpf_validado.cpf}')

    try:
        atleta_out = AtletaOut(id=uuid4(), created_at=datetime.now(), **atleta_in.model_dump())
        atleta_model = AtletaModel(**atleta_out.model_dump(exclude={'categoria', 'centro_treinamento'}))

        atleta_model.categoria_id = categoria.pk_id
        atleta_model.centro_treinamento_id = centro_treinamento.pk_id

        db_session.add(atleta_model)
        await db_session.commit()
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'Ocorreu um erro ao inserir os dados no banco: {exc}')

    return atleta_out

@router.get(
    '/', 
    summary='Consultar todos os atletas', 
    status_code=status.HTTP_200_OK,
    response_model=LimitOffsetPage[AtletaOutPersonalizado]
)
async def query(
    db_session: DatabaseDependency,
    nome: str | None = None,
    cpf: str | None = None,
) -> list[AtletaOutPersonalizado]:
    if nome:
        atletas: list[AtletaOutPersonalizado] = (await db_session.execute(select(AtletaModel).filter_by(nome=nome))).scalars().all()
    elif cpf:
        atletas: list[AtletaOutPersonalizado] = (await db_session.execute(select(AtletaModel).filter_by(cpf=cpf))).scalars().all()
    else:
        atletas: list[AtletaOutPersonalizado] = (await db_session.execute(select(AtletaModel))).scalars().all()
    
    lista_atletas = [AtletaOutPersonalizado.model_validate(atleta) for atleta in atletas]
    return paginate(lista_atletas)

@router.get(
    '/{id}', 
    summary='Consultar um atleta pelo id', 
    status_code=status.HTTP_200_OK,
    response_model=AtletaOut
)
async def query(
    id: UUID4,
    db_session: DatabaseDependency
) -> AtletaOut:
    atleta: AtletaOut = (await db_session.execute(select(AtletaModel).filter_by(id=id))).scalars().first()

    if not atleta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Atleta não encontrado no id: {id}')

    return atleta

@router.patch(
    '/{id}', 
    summary='Editar um atleta pelo id', 
    status_code=status.HTTP_200_OK,
    response_model=AtletaOut
)
async def query(
    id: UUID4,
    db_session: DatabaseDependency,
    atleta_up: AtletaUpdate = Body(...)
) -> AtletaOut:
    atleta: AtletaOut = (await db_session.execute(select(AtletaModel).filter_by(id=id))).scalars().first()

    if not atleta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Atleta não encontrado no id: {id}')
    
    atleta_update = atleta_up.model_dump(exclude_unset=True)

    for key, value in atleta_update.items():
        setattr(atleta, key, value)

    await db_session.commit()
    await db_session.refresh(atleta)

    return atleta

@router.delete(
    '/{id}', 
    summary='Deletar um atleta pelo id', 
    status_code=status.HTTP_204_NO_CONTENT
)
async def query(
    id: UUID4,
    db_session: DatabaseDependency
) -> None:
    atleta: AtletaOut = (await db_session.execute(select(AtletaModel).filter_by(id=id))).scalars().first()

    if not atleta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Atleta não encontrado no id: {id}')
    
    await db_session.delete(atleta)
    await db_session.commit()

add_pagination(router)