DROP TRIGGER trans_acctf_ins_trg ON billservice_transaction;

CREATE OR REPLACE FUNCTION account_transaction_trg_fn()
  RETURNS trigger AS
$BODY$
DECLARE 
  bonus_balance numeric;
  account_ballance numeric;
BEGIN




IF (TG_OP = 'INSERT') THEN 
SELECT INTO account_ballance COALESCE(ballance, 0) FROM billservice_account WHERE id=NEW.account_id;
SELECT INTO bonus_balance COALESCE(bonus_ballance, 0) FROM billservice_account WHERE id=NEW.account_id;

  NEW.prev_balance := account_ballance;
  
  IF (bonus_balance>=NEW.summ*(-1) and NEW.summ<0 and NEW.is_bonus=False) THEN
    bonus_balance := bonus_balance-NEW.summ;
  ELSIF (NEW.summ<0 and NEW.is_bonus=False) THEN
    bonus_balance :=0;
  ELSIF (NEW.is_bonus=True) THEN
    bonus_balance :=bonus_balance+NEW.summ;
  END IF;
  UPDATE billservice_account SET ballance=COALESCE(ballance, 0)+NEW.summ, bonus_ballance=bonus_balance WHERE id=NEW.account_id;
  RETURN NEW;
ELSIF (TG_OP = 'DELETE') THEN
  UPDATE billservice_account SET ballance=COALESCE(ballance, 0)-OLD.summ WHERE id=OLD.account_id;
  RETURN OLD;
ELSIF (TG_OP = 'UPDATE') THEN
  SELECT INTO NEW.prev_balance  COALESCE(ballance, 0) FROM billservice_account WHERE id=NEW.account_id;
  UPDATE billservice_account SET ballance=COALESCE(ballance, 0)-OLD.summ WHERE id=OLD.account_id;
  UPDATE billservice_account SET ballance=COALESCE(ballance, 0)+NEW.summ WHERE id=NEW.account_id;
RETURN NEW;
END IF;
RETURN NULL;
END;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;